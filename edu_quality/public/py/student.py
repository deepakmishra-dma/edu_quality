from edu_quality.overrides import make_payment_request
import time 
from frappe.utils import today
import frappe

def autoname(doc, method=None):
    school_prefixes = {
        "Walnut School at Fursungi": "FU",
        "Walnut School at Shivane": "SH",
        "Walnut School at Wakad": "WA"
    }

    if doc.imported and doc.reference_number:
        prefix = school_prefixes.get(doc.school, '')
        doc_name = prefix + doc.reference_number
        doc.name = doc_name

    if doc.student_applicant:
        applicant = frappe.get_doc("Student Applicant",doc.student_applicant)
        prefix = frappe.get_value("School",applicant.school,'prefix')
        series = get_reference(doc.program)
        prefix += series
        if frappe.db.count("Student",[["name","Like",prefix + "%"]])>=99:
            prefix = prefix[:-2] + chr(ord(prefix[-2]) + 1)
            series = series[0] + chr(ord(series[1])+1)
            frappe.db.set_value("Program",applicant.program,'reference_series',series)
        if not prefix:
            prefix = "EDU-STU-2023-"
        count = frappe.db.count("Student",[["name","Like",prefix + "%"]]) + 1
        if count>9:
            prefix += str(count)
        else:
            prefix += "0" + str(count)
        doc.name = prefix

def before_insert(doc, method=None):
    frappe.flags.in_import = True

def get_reference(program):
    if not frappe.db.get_value("Academic Year",[["Academic Year","year_start_date","<=",today()],["Academic Year","year_end_date",">=",today()]],"rolled_over"):
        current_program = frappe.get_doc("Program",program)
        series = frappe.db.get_value("Program",{'school':current_program.school,"sequence":current_program.sequence-1},'reference_series')
        if not series:
            series = current_program.reference_series
            series = series[0] + chr(ord(series[1])+1) 
    else: 
        series = frappe.db.get_value("Program",program,'reference_series')
    return series

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
                frappe.db.set_value("Fee Schedule Student Group", {"parent":fee_schedule,"student_group":student_group},'total_students',len(st))
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


def create_payment_request(fee,term=None):
    try:
        if not frappe.db.exists(
            "Payment Request",
            {"reference_doctype": "Fees", "reference_docname": fee.name},
        ):
            time.sleep(30)
            make_payment_request(
                party_type="Student",
                party=fee.student,
                dt="Fees",
                dn=fee.name,
                payment_term = term,
                recipient_id=frappe.get_value('Student',fee.student,'student_email_id'),
                submit_doc=True,
                use_dummy_message=True,
            )
    except Exception as e:
        frappe.logger("edu_quality").exception(e)
