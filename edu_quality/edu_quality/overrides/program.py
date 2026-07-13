import base64
import os
import random
from collections import defaultdict

import frappe
import pandas as pd
from education.education.doctype.program.program import Program


class customProgram(Program):
	@frappe.whitelist()
	def get_possible_allocations(self):
		academic_year = frappe.get_value("Academic Year", {"custom_current_academic_year": 1}, "name")
		# get all students in the program
		students = self.get_students(academic_year)
		divisions = frappe.db.get_all(
			"Student Group",
			filters={"program": self.name, "academic_year": academic_year, "disabled": 0},
			fields=["name", "batch", "max_strength"],
		)
		allocation = self.allocate_students_to_divisions(students, divisions)

		# Cache the allocation for 5 minutes
		rs = frappe.cache()
		data = frappe.json.dumps(allocation)
		rs.set(self.name, data, 300)
		return allocation

	@frappe.whitelist()
	def shuffle_divisions(self):
		try:
			data = frappe.cache().get(self.name)
			allocation = frappe.json.loads(data)
			for division, students in allocation.items():
				div = frappe.get_doc("Student Group", division)
				div.students = []
				for student in students:
					div.append(
						"students",
						{
							"student": student.get("name"),
						},
					)
					# update student details after shuffling
					self.update_student_details(student, div)
				div.save()
			self.sync_details()
			return "Division shuffled successfully"
		except Exception as e:
			frappe.log_error("Shuffle Division Data Error", frappe.get_traceback())
			return False

	def allocate_students_to_divisions(self, students, divisions):
		# Group divisions by batch
		divisions_by_batch = defaultdict(list)
		for division in divisions:
			divisions_by_batch[division["batch"]].append(division)

		# Group students by batch, house, and gender
		students_by_batch = defaultdict(lambda: defaultdict(list))
		for student in students:
			students_by_batch[student["batch"]][(student["house"], student["gender"])].append(student)

		# Shuffle students within each house-gender group to ensure randomness
		for batch in students_by_batch:
			for group in students_by_batch[batch]:
				random.shuffle(students_by_batch[batch][group])

		# Allocate students to divisions
		division_allocation = defaultdict(list)
		for batch, batch_students in students_by_batch.items():
			if batch not in divisions_by_batch:
				raise ValueError(f"No divisions available for batch {batch}")

			division_list = divisions_by_batch[batch]
			division_count = len(division_list)
			division_indices = {division["name"]: 0 for division in division_list}

			for group, students_in_group in batch_students.items():
				division_index = 0
				for student in students_in_group:
					while (
						division_indices[division_list[division_index]["name"]]
						>= division_list[division_index]["max_strength"]
					):
						division_index = (division_index + 1) % division_count

					division_allocation[division_list[division_index]["name"]].append(student)
					division_indices[division_list[division_index]["name"]] += 1
					division_index = (division_index + 1) % division_count

		return division_allocation

	def get_students(self, academic_year):
		return frappe.db.sql(
			"""
            SELECT s.name, s.first_name, s.gender, p.name as pname, p.school_house as house, d.batch
            FROM `tabStudent` as s
            LEFT JOIN `tabProgram Enrollment` as p
            ON s.name = p.student
            LEFT JOIN `tabStudent Group` as d
            ON p.student_group = d.name
            WHERE p.program = %s and p.academic_year = %s and s.student_status != 'Cancelled' and s.enabled = 1
            GROUP BY d.batch, p.school_house, s.gender, s.name
            ORDER BY d.batch, p.school_house, s.gender, RAND()
            """,
			(self.name, academic_year),
			as_dict=True,
		)

	@frappe.whitelist()
	def export_student_details(self):
		try:
			data = frappe.cache().get(self.name)
			allocation = frappe.json.loads(data)
			academic_year = frappe.get_value("Academic Year", {"custom_current_academic_year": 1}, "name")
			columns = [
				"Previous Division",
				"New Division",
				"Name",
				"First Name",
				"Gender",
				"House",
				"Batch",
			]
			new_data = []

			for division, students in allocation.items():
				for student in students:
					student_name = student.get("name")
					prev_division = frappe.get_value(
						"Program Enrollment",
						{"student": student_name, "academic_year": academic_year},
						"student_group",
					)
					new_data.append(
						[
							prev_division,
							division,
							student.get("name"),
							student.get("first_name"),
							student.get("gender"),
							student.get("school_house"),
							student.get("batch"),
						]
					)

			division_data = {columns[i]: [row[i] for row in new_data] for i in range(len(columns))}
			# Convert the data to a pandas DataFrame
			df = pd.DataFrame(division_data)
			public_path = frappe.get_site_path("public", "files")
			filename = f"Student Details - {self.name}.csv"
			filepath = os.path.join(public_path, filename)

			df.to_csv(filepath, index=False)
			with open(filepath, "rb") as file:
				filecontent = file.read()

			response = {
				"filename": filename,
				"filecontent": base64.b64encode(filecontent).decode(),
			}

			return response
		except:
			frappe.log_error("Error While Exporting Student Details", frappe.get_traceback())
			return False

	def update_student_details(self, student, division):
		"""
		student: dict
		(name, first_name, gender, house, program_enrollment(pname))
		"""
		# update student group and tiffin rack no in program enrollment
		roll_no = frappe.db.get_value(
			"Student Group Student", {"student": student.get("name")}, "group_roll_number"
		)
		frappe.db.set_value(
			"Program Enrollment",
			student.get("pname"),
			{"student_group": division.name, "tiffin_rack_no": "", "roll_no": roll_no},
		)

	def sync_details(self):
		"""
		This method syncs the division details from the student group to the program enrollment
		and student doctype for the program and enabled student groups.
		"""
		try:
			academic_year = frappe.get_value("Academic Year", {"custom_current_academic_year": 1}, "name")
			students = frappe.db.sql(
				"""
                SELECT
                    student.name AS student,
                    enrollment.name AS enrollment_name,
                    enrollment.student_group AS enrollment_division,
                    student_group.name AS student_group,
                    student_group.student_group_name AS student_group_name
                FROM
                    `tabStudent` AS student
                LEFT JOIN
                    `tabProgram Enrollment` AS enrollment ON student.name = enrollment.student
                LEFT JOIN
                    `tabStudent Group Student` AS group_student ON student.name = group_student.student
                LEFT JOIN
                    `tabStudent Group` AS student_group ON group_student.parent = student_group.name
                WHERE
                    student.name = enrollment.student AND
                    enrollment.program = %s AND
                    enrollment.academic_year = %s AND
                    enrollment.custom_status != 'Cancelled' AND
                    student.enabled = 1 AND
                    student_group.academic_year = %s AND
                    student_group.disabled = 0
                """,
				(self.name, academic_year, academic_year),
				as_dict=True,
			)

			for student in students:
				if student["student_group"] != student["enrollment_division"]:
					frappe.set_value(
						"Program Enrollment",
						student["enrollment_name"],
						"student_group",
						student["student_group"],
					)
					frappe.set_value(
						"Student", student["student"], "custom_division", student["student_group_name"]
					)
		except:
			frappe.log_error("Error While Syncing Division Details", frappe.get_traceback())
