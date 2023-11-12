import frappe 

def execute():
    frappe.db.truncate("Email Queue")
    frappe.db.truncate("Communication")
    frappe.db.truncate("Funnel Task")