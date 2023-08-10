import frappe
from frappe.model.mapper import get_mapped_doc


def before_save(doc,method=None):
    doc.fee_components = []
    doc.application_fees = 0
    if frappe.db.exists("Application Fees List",{'class':doc.program}):
        doc.application_fees = frappe.get_value("Application Fees List",{'class':doc.program},'application_fees')
        doc.append('fee_components',{
            'fees_category': "Application fee",
            'amount': doc.application_fees
        })
    if frappe.db.get_single_value("Fees Settings",'apply_deposits'):
        get_deposits(doc)
    if doc.fee_structure:
        fee_structure = frappe.get_doc("Fee Structure", doc.fee_structure)
        if frappe.db.get_single_value("Fees Settings",'apply_fees'):
            for component in fee_structure.components:
                doc.append('fee_components',{
                    'fees_category':component.fees_category,
                    'amount':component.amount,
                    'description': component.description
                    })
    else:
        frappe.throw("Fee Structure is Mandatory")
    calculate_total(doc)

def calculate_total(doc):
    doc.total_amount = 0
    for component in doc.fee_components:
        if component.amount:
            doc.total_amount += float(component.amount)

def get_deposits(doc):
    deposits = frappe.get_all('Security Deposit',{'program':doc.program,'academic_year':doc.academic_year},['name','amount'])
    for deposit in deposits:
        doc.append('fee_components',{
            'fees_category': "Deposit",
            'amount': deposit.amount
        })
    

@frappe.whitelist()
def enroll_student(source_name):
    """Creates a Student Record and returns a Program Enrollment.

    :param source_name: Student Applicant.
    """
    frappe.publish_realtime(
        "enroll_student_progress", {"progress": [1, 4]}, user=frappe.session.user
    )
    student = get_mapped_doc(
        "Student Applicant",
        source_name,
        {
            "Student Applicant": {
                "doctype": "Student",
                "field_map": {"name": "student_applicant"},
            }
        },
        ignore_permissions=True,
    )
    student.save()

    student_applicant = frappe.get_doc("Student Applicant", source_name)

    program_enrollment = frappe.new_doc("Program Enrollment")
    program_enrollment.student = student.name
    program_enrollment.student_category = student_applicant.student_category
    program_enrollment.student_name = student.student_name
    program_enrollment.school = student_applicant.program
    program_enrollment.program = student_applicant.program
    program_enrollment.academic_year = student_applicant.academic_year
    program_enrollment.academic_term = student_applicant.academic_term
    program_enrollment.student_group = get_student_group(student_applicant)
    program_enrollment.save()
    program_enrollment.submit()
    frappe.publish_realtime(
    	"enroll_student_progress", {"progress": [2, 4]}, user=frappe.session.user
    )
    return program_enrollment

def get_student_group(doc):
    filters = {"academic_year": doc.academic_year, "program": doc.program}
    return frappe.db.get_value("Student Group", filters, "name")