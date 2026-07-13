# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import csv
from io import StringIO

import frappe
import requests
from frappe.utils.nestedset import NestedSet

from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.public.py.utils import extract_year_from_academic_year_name


class DescriptiveQuestion(NestedSet):
	pass


@frappe.whitelist()
def import_descriptive_ques(url):
	try:
		origin = frappe.request.headers.get("Origin")
		full_url = origin + url
		response = requests.get(full_url)
		response.raise_for_status()
		return import_descriptive_question_schedule_background(response.text)

	except Exception as e:
		print(e, "except")
		frappe.log_error(f"Error importing Exam Config: {str(e)}", "Exam Config Import")
		return {"status": "failed", "message": str(e)}


def import_descriptive_question_schedule_background(csv_content):
	errors = []
	try:
		csv_reader = csv.reader(StringIO(csv_content))
		total_rows = sum(1 for _ in csv_reader) - 1  # Excluding header row
		csv_reader = csv.reader(StringIO(csv_content))
		next(csv_reader)  # Skip header row

		for idx, row in enumerate(csv_reader, start=1):
			try:
				acad_year, parent_ques, ques, subject, class_type = row[:5]
				check_and_generate_ques(acad_year, parent_ques, ques, subject, class_type)
				progress = idx * 100 // total_rows
				# Publish progress
				frappe.realtime.publish_progress(
					progress,
					title="Import Questions",
					description=f"{idx}/{total_rows} rows processed",
				)
			except Exception as e:
				err = [idx, str(e)]
				errors.append(err)
				# Rollback changes

		if errors:
			frappe.db.rollback()
			error_message = "Error importing Questions background:<br>"
			error_message += "<table>"
			error_message += "<tr><th>Row No</th><th>Error Message</th></tr>"
			for err in errors:
				error_message += f"<tr><td>{err[0]}</td><td>{err[1]}</td></tr>"
			error_message += "</table>"
			return {"status": "failed", "message": error_message}
		frappe.db.commit()
		return {"status": "success", "message": ("Questions imported successfully")}
	except Exception as e:
		frappe.log_error(
			message=f"Error importing Questions background: {str(e)}",
			title="Questions Import Background",
		)
		return {"status": "failed", "message": str(e)}


def check_and_generate_ques(acad_year, parent_ques, ques, subject, class_type):
	parent_ques_name = frappe.db.get_value(
		"Descriptive Question",
		{
			"academic_year": acad_year,
			"question": parent_ques,
			"subject": subject,
			"class_type": class_type,
		},
	)

	if not frappe.db.exists(
		"Descriptive Question",
		{
			"academic_year": acad_year,
			"parent_descriptive_question": parent_ques_name,
			"question": ques,
			"subject": subject,
			"class_type": class_type,
		},
	):
		doc = frappe.new_doc("Descriptive Question")
		doc.academic_year = acad_year
		doc.parent_descriptive_question = parent_ques_name
		doc.question = ques
		doc.subject = subject
		doc.class_type = class_type
		doc.insert()
