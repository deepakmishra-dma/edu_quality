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
    today = datetime.today().date()
    fee_schedules = frappe.get_all("Fee Schedule")
    for fee_schedule in fee_schedules:
        before_days = frappe.get_value("Fee Schedule",fee_schedule.name,"create_payment_request_before")
        fee_list = frappe.get_all("Fees",{'fee_schedule':fee_schedule.name,'workflow_state':'Approved'})
        for fee in fee_list:
            fee_doc = frappe.get_doc("Fees",fee.name)
            for schedule in fee_doc.payment_schedule:
                if (schedule.due_date - today).days == before_days:
                    frappe.enqueue(
                        "edu_quality.public.py.student.create_payment_request",
                        fee=fee_doc,
                        term = schedule.payment_term,
                        is_async=True,
                        queue="long",
                        timeout=1800,
                    )


def create_payment_request_before_due_date_fee_advance():
    today_date = frappe.utils.getdate(frappe.utils.today())
    fee_advance_docs = frappe.get_all("Fee Advance")
    for fee_advance in fee_advance_docs:
        fee_advance_doc = frappe.get_doc("Fee Advance",fee_advance.name)
        due_date = fee_advance_doc.due_date
        if (due_date - today_date).days < 30:
            schedule_payment_request(fee_advance_doc, fee_advance_doc.payment_term)


def schedule_payment_request(doc, payment_term):
    filters = {
        "reference_name": doc.name,
        "docstatus": 1,
    }
    if doc.docstatus != 1:
        return
    if not frappe.db.exists("Payment Request", filters):
        frappe.enqueue(
            "edu_quality.public.py.student.create_payment_request",
            fee=doc,
            term = payment_term,
            is_async=True,
            queue="long",
            timeout=1800,
        )


def update_academic_year():
    frappe.enqueue(
        "edu_quality.edu_quality.server_scripts.utils.update_academic_year",
    )
