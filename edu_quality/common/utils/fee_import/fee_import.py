import json
import frappe
import requests
from edu_quality.fees.doctype.fee_advance.fee_advance import create_fee_advance

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
    if response.status_code==200:
        data = response.json()
        if data.get("data",[]):
            return data
        else:
            return None

@frappe.whitelist()
def fee_advance():
    try:
        students = frappe.get_all("Student",{"student_status":"Current student"})
        all_len = len(students)
        for index, student in enumerate(students):
            student_doc = frappe.get_doc("Student",student.name)
            p_e_doc = frappe.get_doc("Program Enrollment",{"student": student.name})
            class_name = frappe.get_value("Program",p_e_doc.program,"program_name")
            if not frappe.get_value("Fee Advance",{"student":student.name,"program":class_name}):
                fees = import_fees(institution=student_doc.school,program=class_name,status=student_doc.student_status,financial_year=p_e_doc.academic_year,fee_or_dep="fee")
                if fees:
                    if not check_deu_date_fee(fees,student_doc):
                        frappe.enqueue(create_fee_advance, student=student_doc, program_enrollment=p_e_doc,all_len=all_len,index=index)
                else:
                    frappe.enqueue(create_fee_advance, student=student_doc, program_enrollment=p_e_doc,all_len=all_len,index=index)
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
    frappe.logger("fesss").exception(fees)
    records = fees.get("data",[])
    if records:
        records.get(student_doc.reference_number,[])
        return True
    else:
        return False
