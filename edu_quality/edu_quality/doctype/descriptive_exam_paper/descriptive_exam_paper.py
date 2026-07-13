import csv
import json
from io import StringIO

import frappe
import requests
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.public.py.utils import extract_year_from_academic_year_name


class DescriptiveExamPaper(Document):
	def autoname(self, method=None):
		self.name = name_func(self)

	def before_validate(self):
		if self.get("__unsaved") and self.get("__islocal") and frappe.flags.in_import:
			questions = [question.question for question in self.questions]
			result = add_question(questions)

			for question in result:
				question_name = question.get("name")
				par_ques_name = question.get("parent_descriptive_question")
				if question_name not in questions:
					self.append(
						"questions",
						{"question": question_name, "parent_question": par_ques_name},
					)


@frappe.whitelist()
def name_func(descriptive_exam_doc):
	descriptive_exam_doc = (
		json.loads(descriptive_exam_doc) if isinstance(descriptive_exam_doc, str) else descriptive_exam_doc
	)

	academic_year = extract_year_from_academic_year_name(
		descriptive_exam_doc.get("academic_year") or current_academic_year()
	)
	subject = frappe.get_doc("Course", descriptive_exam_doc.subject)
	class_type = descriptive_exam_doc.get("class_type")

	class_type_doc = frappe.get_doc("Class Type", class_type)

	return f"{descriptive_exam_doc.name1} {subject.get('custom_short_code')}{class_type_doc.short_code} {academic_year}"


# edu_quality.edu_quality.doctype.descriptive_exam_paper.descriptive_exam_paper.add_question
@frappe.whitelist()
def add_question(docnames):
	parsed_docnames = json.loads(docnames) if isinstance(docnames, str) else docnames
	res = get_all_children_of_multiple_docs("Descriptive Question", parsed_docnames)

	return res


def get_all_children(parent_doctype, parent_name, parent_descriptive_question=None):
	"""Recursively fetch all child nodes of a tree document using frappe.qb."""
	ChildDoc = frappe.qb.DocType(parent_doctype)
	children = (
		frappe.qb.from_(ChildDoc)
		.select(ChildDoc.name, ChildDoc.parent_descriptive_question)
		.where(ChildDoc.parent_descriptive_question == parent_name)
		.run(as_dict=True)
	)

	all_children = [
		{"name": parent_name, "parent_question": parent_descriptive_question}
	]  # Include the parent name in the result
	for child in children:
		all_children.append(child)
		child_children = get_all_children(parent_doctype, child["name"], child["parent_descriptive_question"])
		all_children.extend(child_children)
	return all_children


def get_all_children_of_multiple_docs(parent_doctype, parent_names):
	"""Fetch all child nodes of multiple tree documents."""
	all_children = []
	for parent_name in parent_names:
		all_children.extend(get_all_children(parent_doctype, parent_name))
	return deduplicate_dicts(all_children)


def deduplicate_dicts(dicts):
	seen = {}
	deduped_list = []

	for d in dicts:
		name = d["name"]
		if name not in seen:
			seen[name] = True
			deduped_list.append(d)

	return deduped_list


@frappe.whitelist()
def import_exam_paper(url):
	try:
		origin = frappe.request.headers.get("Origin")
		full_url = origin + url
		response = requests.get(full_url)
		response.raise_for_status()
		return import_exam_paper_in_bg(response.text)

	except Exception as e:
		print(e, "except")
		frappe.log_error(f"Error importing Question Paper: {str(e)}", "Question Paper Import")
		return {"status": "failed", "message": str(e)}
	finally:
		# Disconnect database connection
		print("db closed")
		# frappe.db.close()


def gen_bulk_rows(csv_reader, row_no=2):
	bulk_rows = []
	for idx, row in enumerate(csv_reader, start=1):
		name = row[1]
		if name:
			bulk_rows.append([row])

		else:
			bulk_rows[-1].append(row)
	return bulk_rows


def import_exam_paper_in_bg(csv_content):
	errors = []
	try:
		csv_reader = csv.reader(StringIO(csv_content))
		total_rows = sum(1 for _ in csv_reader) - 1  # Excluding header row
		csv_reader = csv.reader(StringIO(csv_content))
		headers = next(csv_reader)  # Skip header row
		bulk_rows = gen_bulk_rows(csv_reader)
		errors = insert_paper_in_db(bulk_rows, headers, total_rows)

		if errors:
			frappe.db.rollback()
			error_message = "Error importing Question Paper background:<br>"
			error_message += "<table>"
			error_message += "<tr><th>Row No</th><th>Error Message</th></tr>"
			for err in errors:
				error_message += f"<tr><td>{err[0]}</td><td>{err[1]}</td></tr>"
			error_message += "</table>"
			frappe.log_error("Error importing Question Papers", str(errors))
			return {"status": "failed", "message": error_message}
		frappe.db.commit()
		return {
			"status": "success",
			"message": ("Question Paper imported successfully"),
		}
	except Exception as e:
		frappe.log_error(
			message=f"Error importing Question Paper background: {str(frappe.get_traceback())}",
			title="Question Paper Import Background",
		)
		return {"status": "failed", "message": str(e)}


def insert_paper_in_db(bulk_data, headers, total_rows):
	errors = []
	try:
		for index, parent_row in enumerate(bulk_data, start=1):
			try:
				current_paper = None
				current_question = None
				current_subject = None
				current_class_type = None
				current_academic_year = None
				for idx, row in enumerate(parent_row, start=1):
					try:
						(
							subject,
							name,
							class_type,
							acad_year,
							question,
							sub_question,
						) = row[:6]
						if name:
							current_subject = subject
							current_class_type = class_type
							current_academic_year = acad_year
							current_paper = frappe.new_doc("Descriptive Exam Paper")
							current_paper.name1 = name
							current_paper.academic_year = current_academic_year
							current_paper.subject = subject
							current_paper.class_type = class_type

						if question:
							insert_question(
								current_paper,
								sub_question,
								question,
								current_subject,
								current_class_type,
							)
							current_question = question

						else:
							if current_question and current_subject and current_class_type:
								insert_question(
									current_paper,
									sub_question,
									current_question,
									current_subject,
									current_class_type,
								)

						progress = idx * 100 // total_rows
						frappe.realtime.publish_progress(
							progress,
							title="Import Exams",
							description=f"{idx}/{total_rows} rows processed",
						)

					except Exception as e:
						err = [idx, str(e)]
						errors.append(err)
				if current_paper:
					current_paper.insert()
			except Exception as e:
				err = [idx, str(e)]
				errors.append(err)
		return errors
	except Exception as e:
		err = [f"Group {index}", str(e)]
		errors.append(err)
		return errors


def insert_question(current_paper, sub_question, question, subject, class_type):
	if sub_question not in current_paper.questions:
		parent_question_name = frappe.db.get_value(
			"Descriptive Question",
			{"question": question, "subject": subject, "class_type": class_type},
		)
		sub_question_name = frappe.db.get_value(
			"Descriptive Question",
			{
				"question": sub_question,
				"subject": subject,
				"class_type": class_type,
				"parent_descriptive_question": parent_question_name,
			},
		)
		if not parent_question_name or not sub_question_name:
			frappe.throw(f"{question} {sub_question} Not found")

		current_paper.append(
			"questions",
			{
				"selected": 1,
				"question": sub_question_name,
				"parent_question": parent_question_name,
			},
		)
