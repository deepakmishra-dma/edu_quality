import frappe 
from frappe.utils import getdate

def on_submit(doc, method=None):
    try:
        doc.db_set("transaction_date",getdate())
        doc.db_set("sent_by",frappe.session.user) 
    except Exception as e:
        frappe.logger('purchase').exception(e)