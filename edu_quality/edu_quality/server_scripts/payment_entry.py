import frappe
from edu_quality.api.google_admin import unsuspend_google_user

def validate(doc, method=None):
    letter_head = None
    if doc.school:
        letter_head = frappe.get_value("School", doc.school, 'letter_head')
    else:
        letter_head = frappe.get_value("Company", doc.company, 'default_letter_head')
    doc.letter_head = letter_head 
    filters = {
        "name": doc.party,
        "student_status": "Defaulter"
    }
    student = frappe.get_value("Student", filters)
    if student:
        student_email_id = frappe.get_value("Student", doc.party, "student_email_id")
        frappe.set_value("Student", doc.party, "student_status", "Current student")
        unsuspend_google_user(student_email_id)