import frappe 
from frappe.model.naming import make_autoname
from erpnext.accounts.doctype.payment_request.payment_request import (
    make_payment_request,
)

def autoname(doc,method=None):
    if doc.custom_imported and doc.custom_reference_number:
        prefix = ''
        if doc.school == "Walnut School at Fursungi":
            prefix = "FU"
        elif doc.school == "Walnut School Shivane":
            prefix = "SH"
        elif doc.school == "Walnut School at Wakad":
            prefix = "WA" 
        doc_name = prefix + doc.custom_reference_number
        doc.name = doc_name

    if doc.student_applicant:
        applicant = frappe.get_doc("Student Applicant",doc.student_applicant)
        prefix = frappe.get_value("School",applicant.school,'prefix')
        series = frappe.get_value("Program",applicant.program,'reference_series')
        prefix += series
        if frappe.db.count("Student",[["name","Like","%prefix%"]])>=99:
            prefix = prefix[:-2] + chr(ord(prefix[-2]) + 1)
            series = series[0] + chr(ord(series[1])+1)
            frappe.db.set_value("Program",applicant.program,'reference_series',series)
        if not prefix:
            prefix = "EDU-STU-2023-"
        prefix += ".##"
        doc.name = make_autoname(prefix)

def update_student_group(p_e_doc,fee_structure=None):
    try:
        student_group = frappe.get_value("Program Enrollment",{"name":p_e_doc,"docstatus":1},'student_group')
        st = get_students_group(student_group)
        if st:
            program_e_d = frappe.get_doc("Student Group",student_group)
            program_e_d.students = []
            for item in st:
                program_e_d.append("students",item)
            program_e_d.save()
            if frappe.db.exists("Fee Schedule",{"fee_structure":fee_structure}):
                fee_schedule = frappe.get_value("Fee Schedule",{"fee_structure":fee_structure})
                doc = frappe.get_doc("Fee Schedule Student Group", {"parent":fee_schedule,"student_group":student_group})
                doc.total_students = len(st)
                doc.save()
        return
    except Exception as e:
        frappe.throw(str(e))


def get_students_group(student_group):
    enrolled_students = frappe.get_all("Program Enrollment",{"student_group":student_group,"docstatus":1},['student','student_name'])
    if enrolled_students:
        student_list = []
        for s in enrolled_students:
            if frappe.db.get_value("Student", s.student, "enabled"):
                s.update({"active": 1})
            else:
                s.update({"active": 0})
            student_list.append(s)
        return student_list
    else:
        return []


def create_payment_request(fees,term=None):
    try:
        for f in fees:
            fee = frappe.get_doc("Fees", f.name)
            if not frappe.db.exists(
                "Payment Request",
                {"reference_doctype": "Fees", "reference_docname": fee.name},
            ):
                make_payment_request(
                    party_type="Student",
                    party=fee.student,
                    dt="Fees",
                    dn=fee.name,
                    payment_term = term,
                    recipient_id=fee.student_email,
                    submit_doc=True,
                    use_dummy_message=True,
                )
    except Exception as e:
        frappe.logger("edu_quality").exception(e)