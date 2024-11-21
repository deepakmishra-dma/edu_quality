import frappe
from edu_quality.edu_quality.server_scripts.payment_plan import change_payment_plan


def execute():
    fees = frappe.db.get_all("Fees", {"docstatus": 1, "payment_plan": ["not like", "%P2%"]}, ["name", "payment_plan"])
    fee_advance = frappe.db.get_all("Fee Advance", {"docstatus": 1, "payment_plan": ["not like", "%P2%"]}, ["name", "payment_plan"])
    for fee in fees:
        not_paid_filter = {"reference_name": fee.name, "status": ["not in", ["Paid", "Cancelled"]]}
        if frappe.db.exists("Payment Request", not_paid_filter):
            change_payment_plan(fee.payment_plan, "Fees", fee.name)

    for fee in fee_advance:
        not_paid_filter = {"reference_name": fee.name, "status": ["not in", ["Paid", "Cancelled"]]}
        if frappe.db.exists("Payment Request", not_paid_filter):
            change_payment_plan(fee.payment_plan, "Fee Advance", fee.name)