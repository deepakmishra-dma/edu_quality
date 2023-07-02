import frappe 

def before_save(doc,method=None):
    if doc.payment_term and doc.reference_doctype=='Fees':
        fees = frappe.get_doc("Fees",doc.reference_name)
        for schedule in fees.payment_schedule:
            if schedule.payment_term == doc.payment_term:
                doc.grand_total = schedule.payment_amount

