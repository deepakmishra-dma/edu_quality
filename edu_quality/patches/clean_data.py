import frappe

def execute():
    frappe.db.truncate("Fees")
    frappe.db.truncate("Program Enrollment")
    frappe.db.commit()