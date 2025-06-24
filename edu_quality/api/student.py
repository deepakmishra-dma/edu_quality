import frappe


@frappe.whitelist(allow_guest=True)
def get_student_data(student):
    student = frappe.get_doc("Student", student, ignore_permissions=True)
    return student.as_dict()
