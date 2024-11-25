import frappe


def validate(doc, method=None):
    letter_head = None
    if doc.school:
        letter_head = frappe.get_value("School", doc.school, 'letter_head')
    else:
        letter_head = frappe.get_value("Company", doc.company, 'default_letter_head')
    doc.letter_head = letter_head 
    filters = {
        "student": doc.party,
        "student_status": "Defaulter",
    }
    if frappe.db.exists("Student",filters):
        stud_doc = frappe.get_doc("Student", filters)
        stud_doc.student_status = "Current student"
        doc.save(ignore_permissions=True)