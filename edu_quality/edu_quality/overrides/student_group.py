import frappe 
from education.education.doctype.student_group.student_group import (
	StudentGroup, get_program_enrollment
)
from frappe.utils import cint
from frappe import _

class CustomStudentGroup(StudentGroup):
	def validate_students(self):
		program_enrollment = get_program_enrollment(
			self.academic_year,
			self.academic_term,
			self.program,
			self.batch,
			self.student_category,
			self.course,
		)
		students = [d.student for d in program_enrollment] if program_enrollment else []
		for d in self.students:
			if (
				(self.group_based_on == "Batch")
				and cint(frappe.defaults.get_defaults().validate_batch)
				and d.student not in students
			):
				frappe.throw(
					_("{0} - {1} is not enrolled in the Batch {2}").format(
						d.group_roll_number, d.student_name, self.batch
					)
				)

			if (
				(self.group_based_on == "Course")
				and cint(frappe.defaults.get_defaults().validate_course)
				and (d.student not in students)
			):
				frappe.throw(
					_("{0} - {1} is not enrolled in the Course {2}").format(
						d.group_roll_number, d.student_name, self.course
					)
				)