import frappe

def execute():
    return
    replace_emails()

def replace_emails():
    data = frappe.db.get_all("Guardian", fields=["name","email_id"])
    for guardian in data:
        new_email = guardian.email_id.split("@")[0] + "@yopmail.com"
        frappe.db.set_value("Guardian",guardian.name,"email_id",new_email)