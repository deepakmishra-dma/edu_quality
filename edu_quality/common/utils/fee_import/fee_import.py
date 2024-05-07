import json
import frappe
import requests
from edu_quality.fees.doctype.fee_advance.fee_advance import create_fee_advance
from edu_quality.common.utils.progress import set_progress

@frappe.whitelist(allow_guest=True)
def import_fees(**kwargs):
    purl = "https://test.walnutedu.in/indexCI.php/fee_due_report/fetch_student_fee_due"
    payload = json.dumps(
        {
            "sch_ins": kwargs.get("institution"),
            "class": kwargs.get("program"),
            "status": kwargs.get("status"),
            "financial_year": kwargs.get("financial_year"),
            "fee_or_dep": kwargs.get("fee_or_dep"),
            "user": "walnutfeecollect",
            "password": "***REMOVED-PASSWORD***",
        }
    )
    response = requests.post(purl, data=payload)
    data = response.json()
    frappe.logger("fesss").exception(data)
    if data.get("data"):
        return  data
    elif data.get('message',None) =="Student Not Found!" or data.get('message',None) == None:
        return None

@frappe.whitelist()
def fee_advance():
    students = frappe.get_all("Student",filters=[["student_status","in",["Current student"]]])
    all_len = len(students)
    for index, student in enumerate(students):
        frappe.enqueue(import_fee,student=student,index=index,all_len=all_len)

def import_fee(student,index,all_len):
    try:
        set_progress(index + 1, all_len,1, "Student Details")
        student_doc = frappe.get_doc("Student",student.name)
        p_e_doc = frappe.get_doc("Program Enrollment",{"student": student.name})
        class_name = frappe.get_value("Program",p_e_doc.program,"program_name")
        if not frappe.get_value("Fee Advance",{"student":student.name,"program":class_name}):
            ins_id = get_institution(student_doc.school)
            fees = import_fees(institution=ins_id,program=class_name,status=student_doc.student_status,financial_year=p_e_doc.academic_year,fee_or_dep="fee")
            if fees:
                if not check_deu_date_fee(fees,student_doc):
                    create_log(student_doc.name,class_name,student_doc.school)
                    # frappe.enqueue(create_log,student=student_doc.name,class_name=class_name,school=student_doc.school)
                    # frappe.enqueue(create_fee_advance, student=student_doc, program_enrollment=p_e_doc,all_len=all_len,index=index)
            else:
                create_log(student_doc.name,class_name,student_doc.school)
                # frappe.enqueue(create_fee_advance, student=student_doc, program_enrollment=p_e_doc,all_len=all_len,index=index)
    except Exception as e:
        frappe.logger("fee_advance").exception(e)
        cleaned_data = student
        error_obj={
                "filename":"fee_advance",
                "object": cleaned_data,
                "Traceback": frappe.get_traceback(),
            },
        frappe.log_error(
        title="Fee Advance with import",
        message=json.dumps(error_obj),
        )
    
def check_deu_date_fee(fees,student_doc):
    records = fees.get("data",[])
    if records:
        check = records.get(student_doc.reference_number,[])
        if check:
            return True
        else:
            return False
    else:
        return False

def get_institution(ins_id):
    data = {"Walnut School at Shivane":"Rethink Educational Systems Pvt Ltd Shivane",
            "Walnut School at Wakad":"Rethink Educational Systems Pvt Ltd Wakad",
            "Walnut School at Fursungi":"Rethink Educational Systems Pvt Ltd Fursungi"}
    return data.get(ins_id)

def create_log(student,class_name,school):
    if not frappe.db.exists("Fee Advance Current Student",{"student":student, "class_name":class_name,"school":school}):
        doc = frappe.new_doc("Fee Advance Current Student")
        doc.student = student
        doc.class_name = class_name
        doc.school = school
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return