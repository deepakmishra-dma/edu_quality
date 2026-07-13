# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import functions as fn

from edu_quality.public.py.utils import get_div_students


def get_columns(filters=None):
	default_columns = [
		{"fieldname": "student", "label": "Ref No"},
		{"fieldname": "student_name", "label": "Name"},
		# {"fieldname": "subject_rank", "label": "Subject Rank"},
		{"fieldname": "division_rank", "label": "Division Rank"},
		{"fieldname": "class_rank", "label": "Class Rank"},
	]
	return default_columns


def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data


def get_data(filters=None):
	assessment_group = filters.get("assessment_group")
	academic_year = filters.get("academic_year")
	program = filters.get("program")

	assessment_group_doc = frappe.get_doc("Assessment Group", filters.get("assessment_group"))

	divisions = frappe.get_all(
		"Assessment Plan",
		filters={"assessment_group": assessment_group_doc.name},
		fields=["student_group"],
	)
	div_list = [div.get("student_group") for div in divisions]

	students = get_div_students(div_list)
	student_list = [student.get("student") for student in students]
	student_hash = {student.get("student"): student for student in students}
	results = frappe.db.get_all(
		"Assessment Group Result",
		filters={
			"student": ["in", student_list],
			"academic_year": academic_year,
			"assessment_group": assessment_group,
			"program": program,
			"docstatus": 1,
		},
		fields=["student", "class_rank", "division_rank"],
	)
	for res in results:
		student = res.get("student")
		if student in student_hash:
			res["student_name"] = student_hash[student_hash].get("student_name")

	return results
