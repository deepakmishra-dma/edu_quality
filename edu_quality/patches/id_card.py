import frappe
from edu_quality.public.py.fee import create_id_card

def execute():
    program_enrollments = frappe.get_all("Program Enrollment", filters={"docstatus": ["!=", 2]}, fields=["name", "custom_id_card"])

    for pe in program_enrollments:
        id_card = frappe.get_value('Student ID Card', {"program_enrolled_in": pe.name}, "name")
        doc = frappe.get_doc('Program Enrollment', pe.name)
        if not id_card:
            create_id_card(doc)
        else:
            if not doc.custom_id_card:
                doc.custom_id_card = id_card
                doc.save()