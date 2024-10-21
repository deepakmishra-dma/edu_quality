import frappe 


def student_query(user):
    user = frappe.session.user
    roles = frappe.get_roles(frappe.session.user)
    if "Guardian" in roles and "Administrator" not in roles:
        pass