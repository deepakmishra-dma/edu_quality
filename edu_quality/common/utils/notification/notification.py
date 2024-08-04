import frappe

def create_notification_log(variables):
    doc = variables.get("doc")
    fee = frappe.get_doc(doc.reference_doctype, doc.reference_name)
    if doc.payment_term and fee.doctype == "Fees":
        due_date = frappe.get_value("Payment Schedule",{'parent':fee.name,'payment_term':doc.payment_term},'due_date')
    else:
        due_date = fee.due_date
    subject = f"Payment Reminder sent to {fee.student}"
    email_content = f"""
        Payment reminders sent successfully to {fee.student} for {fee.doctype}\n
        <b>Due Date: </b>{due_date}\n
    """
    user = frappe.get_value("Student", fee.student, "user")

    notification_log = frappe.get_doc({
        "doctype": "Notification Log",
        "subject": subject,
        "email_content": email_content,
        "document_type": fee.doctype,
        "document_name": fee.name,
        "type": "Alert",
        "user": user,
    })
    notification_log.insert(ignore_permissions=True)

