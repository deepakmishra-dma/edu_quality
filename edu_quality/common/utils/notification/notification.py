import frappe

def create_notification_log(variables):
    doc = variables.get("doc")
    fee = frappe.get_doc(doc.reference_doctype, doc.reference_name)
    if doc.payment_term and fee.doctype == "Fees":
        due_date = frappe.get_value("Payment Schedule",{'parent':fee.name,'payment_term':doc.payment_term},'due_date')
    else:
        due_date = fee.due_date
    school = fee.custom_school if fee.doctype == "Fees" else fee.school
    subject = f"Payment Reminder For {fee.student}"
    email_content = f"""
        Dear {fee.student},\n
        This is the reminder for the payment of <b>{fee.name}</b>.\n
        <b>School: </b>{school}\n
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
        "type": "Alert",
        "for_user": user,
        "student": fee.student,
        "school": school,
        "class": fee.program,
        "academic_year": fee.academic_year,
        "payment_term": doc.payment_term
    })
    notification_log.insert(ignore_permissions=True)
    notification_log.document_type = notification_log.doctype
    notification_log.document_name = notification_log.name
    notification_log.save(ignore_permissions=True)


def create_notification_log_for_counselor(variables):
    doc = variables.get("doc")
    student_applicant = frappe.get_doc(doc.doctype, doc.name)
    subject = f"Student Application Completion For {student_applicant.first_name} {student_applicant.last_name}"
    url = get_url()
    email_content = (
        "Student Application Completion"
    )

    doc = {
        "type": "Assignment",
        "document_type": "Student Applicant",
        "subject": subject,
        "document_name": doc.name,
        "email_content": email_content,
    }
    user = frappe.session.user
    notification = frappe.new_doc("Notification Log")
    notification.update(doc)
    notification.for_user = user
    notification.insert(ignore_permissions=True)



def check_user_role(variables):
    doc = variables.get("doc")
    check_role = True
    if "Guardian" in frappe.get_roles(frappe.session.user):
        check_role = True
    else:
        check_role = False
    variables['check_role'] = check_role
