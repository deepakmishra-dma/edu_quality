import json
import frappe
import requests


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
    data = response.json()["data"]
    # status = fee_import_handler(data)
    return data


def fee_import_handler(data):
    key_list = list(data.keys())
    key = key_list[0]
    # for key in key_list[0]:
    fee_data = data[key]
    year_head_data = fee_data["0"]["0"]["year_head_data"]
    fee_head_name = year_head_data["fee_head_name"]
    fee_head_amt = year_head_data["fee_head_amt"]
    academic_year = year_head_data["financial_year"]
    class_name = year_head_data["class_name"]
    institution = year_head_data["instt_name"]
    school = year_head_data["school_name"]
    payplan_name = year_head_data["payplan_name"]
    installment_name = fee_data["installment_name"]
    ref_no = fee_data["refno"]
    student, student_name = frappe.get_value("Student", {"ref_no": ref_no}, ['name', 'student_name'])
    program = frappe.get_value("Program", {"name": class_name}, ['name'])

    doc = frappe.get_doc(
        {
            "doctype": "Fees",
            "student": student,
            "student_name": student_name,
            "academic_year": academic_year,
            "program": program,
            "institution": institution,
            "school": school,
        }
    )
    doc.append("components", {"fees_category": fee_head_name, "amount": fee_head_amt})
    doc.save(ignore_permissions=True)

    return True