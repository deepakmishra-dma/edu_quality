import frappe

from frappe.utils import getdate
import datetime
from erpnext.accounts.doctype.payment_request.payment_request import get_gateway_details
from erpnext.accounts.party import get_party_bank_account
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)


@frappe.whitelist()
def validate_bank_account(student):
    return frappe.db.exists("Bank Account", {"party": student})

@frappe.whitelist()
def cancel_student(student,academic_year,fee_collection):
    try:
        if frappe.db.exists("Program Enrollment",{'student':student,'academic_year':academic_year,'docstatus':1}):
            frappe.db.set_value("Program Enrollment",{'student':student,'academic_year':academic_year,'docstatus':1},'docstatus',2)
        frappe.db.set_value("Student",student,'enabled',0)
        frappe.db.set_value("Student",student,"student_status","Cancelled")
        fees_list = frappe.db.get_all("Fees",filters={'docstatus':1,'student':student})
        for fee in fees_list:
            if frappe.db.exists("Fee Component",[['parent','=',fee.name],['fees_category','like','%DEPOSIT%']]):
                deposit = frappe.db.get_value("Fee Component",[['parent','=',fee.name],['fees_category','like','%DEPOSIT%']],'amount')
                refund_deposit(student,fee.name,deposit)
        return 1
    except Exception as e:
        frappe.logger("Cancel").exception(e)
        return 0

def refund_deposit(student,fee,amount):
    gateway_account = get_gateway_details({}) or frappe._dict()
    pr = frappe.new_doc("Payment Request")
    ref_doc = frappe.get_doc("Fees",fee)
    bank_account = (
        get_party_bank_account("Student", student)
    )
    pr.update(
        {
            "payment_gateway_account": gateway_account.get("name"),
            "payment_gateway": gateway_account.get("payment_gateway"),
            "payment_account": gateway_account.get("payment_account"),
            "payment_channel": gateway_account.get("payment_channel"),
            "payment_request_type": "Outward",
            "currency": "INR",
            "grand_total": amount,
            "email_to": student+"@walnutedu.in",
            "subject": "Deposit Refund For for {0}".format(student),
            "message": "Deposit Refund",
            "reference_doctype": "Fees",
            "reference_name": fee,
            "party_type": "Student",
            "party": student,
            "bank_account": bank_account,
            "company": ref_doc.get("company"),
        }
    )

    # Update dimensions
    pr.update(
        {
            "cost_center": ref_doc.get("cost_center"),
            "project": ref_doc.get("project"),
        }
    )

    for dimension in get_accounting_dimensions():
        pr.update({dimension: ref_doc.get(dimension)})

    pr.insert(ignore_permissions=True)
    pr.submit()


@frappe.whitelist()
def mark_entry(student, status, reason=None, date=None, time=None):
    if not date:
        date = getdate()
    if not time:
        time = datetime.datetime.now().strftime("%H:%M:%S")

    try:
        if frappe.db.exists("Attendance Entry", {"student": student, "date": date}):
            entry = frappe.get_doc(
                "Attendance Entry", {"student": student, "date": date}
            )
            entry.append(
                "absent_and_delays",
                {
                    "reason": reason,
                    "status": status,
                    "timestamp": date + " " + time,
                    "user": frappe.session.user,
                },
            )
            entry.flags.ignore_mandatory = True
            entry.save(ignore_permissions=True)
        else:
            entry = frappe.new_doc("Attendance Entry")
            entry.student = student
            entry.date = date
            entry.append(
                "absent_and_delays",
                {
                    "reason": reason,
                    "status": status,
                    "timestamp": date + " " + time,
                    "user": frappe.session.user,
                },
            )
            entry.insert(ignore_permissions=True)
        return True
    except Exception as e:
        frappe.logger("entry").exception(e)
        return False
