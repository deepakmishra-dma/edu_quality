import frappe


def cron():
    frappe.msgprint("Scheduler for MySQL is running")
    frappe.enqueue("edu_quality.mysql.migrate_mysql", queue="long", timeout=1500)
