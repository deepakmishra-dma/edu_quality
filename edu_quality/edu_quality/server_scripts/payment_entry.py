import frappe

from edu_quality.api.google_admin import unsuspend_google_user


def validate(doc, method=None):
	ref_doc = frappe.get_doc(doc.reference_doctype, doc.reference_name)
	doc.letter_head = get_letter_head(ref_doc)
	filters = {"name": doc.party, "student_status": "Defaulter"}
	student = frappe.get_value("Student", filters, ["name", "student_email_id"], as_dict=True)
	if student:
		to_update = {"student_status": "Current student", "enabled": 1}
		frappe.db.set_value("Student", student.name, to_update)
		unsuspend_google_user(student.student_email_id)


def get_letter_head(doc):
	program_name = doc.program if doc.doctype == "Fees" else doc.next_program
	if program_name:
		return frappe.get_value("Program", program_name, "letter_head")
	if doc.school:
		return frappe.get_value("School", doc.school, "letter_head")
	return frappe.get_value("Company", doc.company, "default_letter_head")
