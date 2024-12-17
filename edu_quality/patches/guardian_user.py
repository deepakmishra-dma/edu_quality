import frappe
from edu_quality.edu_quality.server_scripts.guardian import create_user

def execute():
    return
    guardians = frappe.get_all("Guardian", fields=["name","email_address"])
    frappe.flags.in_import = True
    for guardian in guardians:
        if guardian.email_address:
            doc = frappe.get_doc("Guardian", guardian.name)
            try:
                create_user(doc,patch=1)
                # set_student_permissions(doc)
            except Exception as e:
                print(e)
    frappe.flags.in_import = False
