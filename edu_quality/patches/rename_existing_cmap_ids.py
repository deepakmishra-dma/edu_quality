import frappe
def execute():
    data = frappe.db.get_all("CMAP")
    for i in data:
        name = i.get("name")
        frappe.utils.random_string(5)
        
        frappe.rename_doc("CMAP",name,frappe.utils.random_string(6))