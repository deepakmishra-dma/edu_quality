import frappe
from datetime import datetime


def cron():
    config = frappe.get_site_config()
    databases = config.get("databases")
    for database in databases:
        frappe.enqueue(
            "edu_quality.mysql.migrate_mysql",
            database=database,
            is_async=True,
            queue="long",
            enqueue_after_commit=True,
            at_front=True,
        )


def time_based():
    frappe.enqueue(
        "edu_quality.discount.time_based_discount",
        is_async=True,
        queue="long",
        timeout=1800,
    )


def create_payment_request_before_due_date():
    before_days = frappe.db.get_single_value("Fees Settings", "before_days")
    today = frappe.utils.nowdate()
    today = datetime.date(datetime.strptime(today, "%Y-%m-%d"))
    fee_schedule = frappe.get_all("Fee Schedule")
    for f in fee_schedule:
        fs = frappe.get_doc("Fee Schedule", f.name)
        if fs.due_date:
            if (fs.due_date - today).days < before_days:
                fees = frappe.get_all(
                    "Fees",
                    {
                        "fee_structure": fs.fee_structure,
                        "docstatus": 1,
                        "outstanding_amount": [">", 0],
                    },
                )
                frappe.enqueue(
                    "edu_quality.public.py.student.create_payment_request",
                    fees=fees,
                    is_async=True,
                    queue="long",
                    timeout=1800,
                )
