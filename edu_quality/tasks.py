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
            for schedule in fee.payment_schedule:
                if (schedule.due_date - today).days == before_days:
                    frappe.enqueue(
                        "edu_quality.public.py.student.create_payment_request",
                        fees=fee,
                        term = schedule.payment_term,
                        is_async=True,
                        queue="long",
                        timeout=1800,
                    )
