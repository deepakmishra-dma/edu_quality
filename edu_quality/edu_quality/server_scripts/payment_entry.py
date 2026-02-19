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
    student = frappe.get_value("Student", filters, ["name", "student_email_id"], as_dict=True)
    if student:
        to_update = {
            "student_status": "Current student",
            "enabled": 1
        }
        frappe.db.set_value("Student", student.name, to_update)
        unsuspend_google_user(student.student_email_id)