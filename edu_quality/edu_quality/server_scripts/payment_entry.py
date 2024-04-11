import frappe


def validate(doc, method=None):
    letter_head = None
    if doc.school:
        letter_head = frappe.get_value("School", doc.school, 'letter_head')
    else:
        letter_head = frappe.get_value("Company", doc.company, 'default_letter_head')
    doc.letter_head = letter_head 