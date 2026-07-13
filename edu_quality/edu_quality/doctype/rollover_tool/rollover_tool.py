# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from education.education.api import enroll_student
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from edu_quality.edu_quality.server_scripts.utils import (
	current_academic_year,
	mark_rolled_over,
	next_academic_year,
	shift_reference_series,
)


class RolloverTool(Document):
	@frappe.whitelist()
	def get_current_academic_year(self):
		return current_academic_year()

	@frappe.whitelist()
	def shift_series(self):
		shift_reference_series(self.school)

	@frappe.whitelist()
	def mark_rolled(self):
		mark_rolled_over(next_academic_year(self.academic_year))

	@frappe.whitelist()
	def get_students(self):
		students = []
		if not self.get_students_from:
			frappe.throw(_("Mandatory field - Get Students From"))
		elif not self.program:
			frappe.throw(_("Mandatory field - Program"))
		elif not self.academic_year:
			frappe.throw(_("Mandatory field - Academic Year"))
		else:
			condition = "and academic_term=%(academic_term)s" if self.academic_term else " "
			if self.get_students_from == "Student Applicant":
				students = frappe.db.sql(
					f"""select name as student_applicant, title as student_name from `tabStudent Applicant`
					where application_status="Approved" and program=%(program)s and academic_year=%(academic_year)s {condition}""",
					self.as_dict(),
					as_dict=1,
				)
			elif self.get_students_from == "Program Enrollment":
				condition2 = "and student_batch_name=%(student_batch)s" if self.student_batch else " "
				students = frappe.db.sql(
					f"""select student, student_name, student_batch_name, student_category from `tabProgram Enrollment`
					where program=%(program)s and academic_year=%(academic_year)s {condition} {condition2} and docstatus != 2""",
					self.as_dict(),
					as_dict=1,
				)

				student_list = [d.student for d in students]
				if student_list:
					inactive_students = frappe.db.sql(
						"""
						select name as student, student_name from `tabStudent` where name in (%s) and enabled = 0"""
						% ", ".join(["%s"] * len(student_list)),
						tuple(student_list),
						as_dict=1,
					)

					for student in students:
						if student.student in [d.student for d in inactive_students]:
							students.remove(student)

		if students:
			return students
		else:
			frappe.throw(_("No students Found"))

	def validate_rolled_over(self):
		yr = next_academic_year(self.academic_year)
		if frappe.db.get_value("Academic Year", yr, "rolled_over"):
			frappe.throw(_("Academic Year {0} is already rolled over").format(yr))

	@frappe.whitelist()
	def enroll_students(self):
		self.validate_rolled_over()
		total = len(self.students)
		if not total:
			return self.school_wise()

		for i, stud in enumerate(self.students):  # edge cases(senior.others) - manual assignment
			frappe.publish_realtime(
				"program_enrollment_tool", dict(progress=[i + 1, total]), user=frappe.session.user
			)
			if stud.student:
				prog_enrollment = frappe.new_doc("Program Enrollment")
				prog_enrollment.student = stud.student
				prog_enrollment.student_name = stud.student_name
				prog_enrollment.program = stud.next_class
				prog_enrollment.academic_year = next_academic_year()
				prog_enrollment.student_group = stud.next_division
				prog_enrollment.save()
				# prog_enrollment.submit()
		frappe.msgprint(_("{0} Students have been enrolled").format(total))

	def fees_setup_validation(self, programs):
		year = next_academic_year(self.academic_year)
		errors = []
		for program in programs:
			if not frappe.db.exists("Fee Schedule", {"program": program.name, "academic_year": year}):
				errors.append(program.name)
		if errors:
			frappe.throw(_("Fees Setup is not done for the following classes - {}".format(", ".join(errors))))

	def school_wise(self):
		try:
			programs = frappe.get_all(
				"Program",
				filters={"school": self.school, "class_group": self.class_group},
				fields=["name", "sequence", "school"],
				order_by="sequence",
			)
			i = 0
			total = len(programs)
			self.fees_setup_validation(programs)
			for program in programs:
				next_program = None
				error_data = []
				frappe.publish_realtime(
					"program_enrollment_tool", dict(progress=[i + 1, total]), user=frappe.session.user
				)
				# skip senior kg and last class in school
				if "Senior KG" in program.name:
					continue  # manual case
				elif i == len(programs) - 1:
					if not frappe.db.exists(
						"Program", {"school": self.school, "sequence": program.sequence + 1}
					):
						continue  # last class
					else:
						next_program = frappe.db.get_value(
							"Program",
							{"school": self.school, "sequence": program.sequence + 1},
							["name", "sequence", "school"],
							as_dict=True,
						)
				next_program = next_program or programs[i + 1]

				next_yr = next_academic_year(self.academic_year)
				students = self.get_program_students(program.name)
				for j, student in enumerate(students):
					division = self.get_division(student, next_program.name)
					if not division:
						error_data.append(
							{
								"student": student.student,
								"student_name": student.student_name,
								"current_class": program.name,
								"next_class": next_program.name,
								"current_division": frappe.db.get_value(
									"Program Enrollment",
									{"student": student.student, "academic_year": self.academic_year},
									"student_group",
								),
							}
						)
					else:
						if not frappe.db.exists(
							"Program Enrollment", {"student": student.student, "academic_year": next_yr}
						):
							prog_enrollment = frappe.new_doc("Program Enrollment")
							prog_enrollment.student = student.student
							prog_enrollment.student_name = student.student_name
							prog_enrollment.program = next_program.name
							prog_enrollment.academic_year = next_yr
							prog_enrollment.student_group = division
							prog_enrollment.save()
							if not student.possible_dropout:
								# prog_enrollment.submit()
								frappe.db.set_value(
									"Student", student.student, "student_status", "Current student"
								)
				i += 1
				if error_data:
					self.add_to_table(error_data)
		except Exception as e:
			frappe.logger("enrollment").exception(e)

	def add_to_table(self, data):
		for i in data:
			self.append("students", i)
		self.save()

	def get_program_students(self, program):
		query = f"""
					SELECT pe.student, pe.student_name,  pe.student_group, pe.program,`tabStudent`.possible_dropout from
						`tabProgram Enrollment` as pe
					LEFT JOIN `tabProgram` ON pe.program = `tabProgram`.name
					LEFT JOIN `tabStudent` ON pe.student = `tabStudent`.name
					WHERE pe.program="{program}" AND pe.academic_year="{self.academic_year}"
					AND `tabStudent`.enabled = 1 AND confirm_for_next_year = "Yes"
					ORDER BY `tabProgram`.sequence
				"""
		result = frappe.db.sql(query, as_dict=1)
		return result

	def get_division(self, student, next_class):
		division = str(student.student_group[0])
		filters = {
			"academic_year": next_academic_year(self.academic_year),
			"program": next_class,
			"student_group_name": division,
		}

		if frappe.db.exists("Student Group", filters):
			group, max_strength = frappe.db.get_value("Student Group", filters, ["name", "max_strength"])
			if frappe.db.count("Program Enrollment", {"student_group": group}) < max_strength:
				return group
		return None
