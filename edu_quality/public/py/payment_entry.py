import frappe
from frappe.model.naming import make_autoname


def autoname(doc, method=None):
    payment_request = frappe.get_doc("Payment Request", doc.reference_no)
    fee = frappe.get_doc("Fees", payment_request.reference_name)
    student_ref_no = frappe.get_value("Student", fee.student, "custom_reference_number")
    school_code = frappe.get_value("School", fee.custom_school, "prefix")
    year = fee.academic_year
    naming_format = f"{school_code}-{student_ref_no}-({year})-"
    doc.name = make_autoname(naming_format + ".#####", ignore_validate=True)