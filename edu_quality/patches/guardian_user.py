import frappe
from edu_quality.edu_quality.server_scripts.guardian import create_user, set_student_permissions


def execute():
    guardians = frappe.get_all("Guardian",limit=100)
    frappe.flags.in_import = True
    for guardian in guardians:
        doc = frappe.get_doc("Guardian", guardian.name)
        try:
            create_user(doc)
            # set_student_permissions(doc)
        except Exception as e:
            print(e)
    frappe.flags.in_import = False
