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
        Dear {fee.student},\n
        This is the reminder for the payment of <b>{fee.name}</b>.\n
        <b>School: </b>{fee.custom_school}\n
        <b>Class: </b>{fee.program}\n
        <b>Academic Year: </b>{fee.academic_year}\n
        <b>Term: </b>{doc.payment_term}\n
        <b>Amount: </b>{doc.grand_total}\n
        <b>Due Date: </b>{due_date}\n
        Click here to make the payment: <a href="{doc.payment_url}">Make Payment</a>\n
        Please make the payment on time to avoid any inconvenience.\n
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
        "student": fee.student,
        "school": fee.custom_school,
        "class": fee.program,
        "academic_year": fee.academic_year,
        "payment_term": doc.payment_term
    })
    notification_log.insert(ignore_permissions=True)

