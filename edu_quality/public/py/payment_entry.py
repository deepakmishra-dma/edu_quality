import frappe
from frappe.model.naming import make_autoname


def get_naming_format(doctype, docname):
    fee = frappe.get_doc(doctype, docname)
    student_ref_no = frappe.get_value("Student", fee.student, "reference_number")
    school_code = frappe.get_value("School", fee.custom_school if doctype == "Fees" else fee.school, "prefix")
    year = fee.academic_year
    return f"{school_code}-{student_ref_no}-{year}-"

def autoname(doc, method=None):
    payment_request = frappe.get_doc("Payment Request", doc.reference_no)
    if payment_request.reference_doctype in ["Fees", "Fee Advance"]:
        naming_format = get_naming_format(payment_request.reference_doctype, payment_request.reference_name)
        doc.name = make_autoname(naming_format + ".#####")