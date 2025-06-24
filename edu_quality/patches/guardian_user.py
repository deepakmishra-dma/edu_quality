import frappe
from edu_quality.edu_quality.server_scripts.guardian import create_user

# def execute():
#     return
#     guardians = frappe.get_all("Guardian", fields=["name","email_address"])
#     frappe.flags.in_import = True
#     for guardian in guardians:
#         if guardian.email_address:
#             doc = frappe.get_doc("Guardian", guardian.name)
#             try:
#                 create_user(doc,patch=1)
#                 # set_student_permissions(doc)
#             except Exception as e:
#                 print(e)
#     frappe.flags.in_import = False

def execute():
    """
    This patch will create User Permission for Guardians
    """
    guardian_list = frappe.db.get_all("Guardian", ["name","user"])
    for guardian in guardian_list:
        if not guardian.user:
            continue
        if not frappe.db.exists("User Permission",{"user":guardian.user,"allow":"Guardian","for_value":guardian.name}):
            perm = frappe.new_doc("User Permission")
            perm.user = guardian.user
            perm.allow = "Guardian"
            perm.for_value = guardian.name
            perm.insert(ignore_permissions=True)