import csv

import frappe
from frappe.core.doctype.communication.email import make as create_email


def render_jinja(text, object):
    if not text:
        return ""
    if not object:
        return text
    return frappe.render_template(text, object)


def enqueued_specific_notice_docs(__args):
    csv_file = __args.get("csv_file")
    subject = __args.get("subject")
    content = __args.get("notice")

    csv_text = frappe.get_doc("File", {
        "file_url": csv_file,
    }, limit=1).get_content()

    csv_data = csv.DictReader(csv_text.splitlines())
    csv_data = list(csv_data)

    success_ref_ids = []
    failure_ref_ids = []
    failure_texts = []
    for row in csv_data:
        try:
            student_ref_id = row["student_ref_id"]
            student = frappe.get_doc("Student", {"reference_number": student_ref_id})
            data = {
                **student.as_dict(),
                **row
            }
            notice_subject = render_jinja(subject, data)
            notice_content = render_jinja(content, data)
            frappe.get_doc({
                "doctype": "School Notice",
                "student": student.name,
                "subject": notice_subject,
                "notice": notice_content
            }).insert()
            success_ref_ids.append(student_ref_id)
        except Exception as e:
            failure_ref_ids.append(row.get("student_ref_id"))
            failure_texts.append(e)


def enqueued_specific_notice_emails(__args):
    csv_file = __args.get("csv_file")
    subject = __args.get("subject")
    content = __args.get("notice")
    bcc_email_groups = __args.get("bcc_email_groups")

    csv_text = frappe.get_doc("File", {
        "file_url": csv_file,
    }, limit=1).get_content()

    bcc_emails = []
    if bcc_email_groups:
        for bcc_email_group in bcc_email_groups:
            bcc_emails = bcc_emails + [eg.email for eg in frappe.get_all(
                "Email Group Member",
                filters={"email_group": bcc_email_group},
                fields=["email"]
            )]
        # remove duplicates from bcc_emails
        bcc_emails = list(set(bcc_emails))

    csv_data = csv.DictReader(csv_text.splitlines())
    csv_data = list(csv_data)

    success_ref_ids = []
    failure_ref_ids = []
    failure_texts = []
    for row in csv_data:
        try:
            student_ref_id = row["student_ref_id"]
            student = frappe.get_doc("Student", {"reference_number": student_ref_id})
            data = {
                **student.as_dict(),
                **row
            }
            notice_subject = render_jinja(subject, data)
            notice_content = render_jinja(content, data)
            student_email = student.student_email_id
            create_email(
                recipients=[student_email],
                subject=notice_subject,
                content=notice_content,
                bcc=bcc_emails,
                send_email=True,
                read_receipt=True,
            )
            bcc_emails = []
            success_ref_ids.append(student_ref_id)
        except Exception as e:
            failure_ref_ids.append(row.get("student_ref_id"))
            failure_texts.append(e)


@frappe.whitelist()
def create_notice(**kwargs):
    has_csv = kwargs.get("has_csv")
    csv_file = kwargs.get("csv_file")
    subject = kwargs.get("subject")
    content = kwargs.get("notice")
    send_emails = kwargs.get("send_emails")
    bcc_email_groups = kwargs.get("bcc_email_groups")

    # verify supplied data
    if has_csv:
        csv_text = frappe.get_doc("File", {
            "file_url": csv_file,
        }, limit=1).get_content()

        if not csv_text:
            raise frappe.exceptions.ValidationError("CSV File not found")

    if not subject:
        raise frappe.exceptions.MandatoryError("Subject is required")

    if not content:
        raise frappe.exceptions.MandatoryError("Content is required")

    if send_emails:
        if not bcc_email_groups:
            raise frappe.exceptions.MandatoryError("BCC Email Groups are required")

        for bcc_email_group in bcc_email_groups:
            if not frappe.db.exists("Email Group", bcc_email_group):
                raise frappe.exceptions.ValidationError(f"BCC Email Group {bcc_email_group} not found")

    frappe.enqueue(
        enqueued_specific_notice_docs,
        __args=kwargs
    )

    if send_emails:
        frappe.enqueue(
            enqueued_specific_notice_emails,
            queue="long",
            __args=kwargs
        )


@frappe.whitelist()
def send_test_mail(**kwargs):
    has_csv = kwargs.get("has_csv")
    student_data = kwargs.get("student_data")
    subject = kwargs.get("subject")
    content = kwargs.get("notice")
    test_emails = kwargs.get("emails")
    if not test_emails:
        raise frappe.exceptions.MandatoryError("Test Emails are required")

    notice_subject = subject
    notice_content = content

    if has_csv:
        student_ref_id = student_data["student_ref_id"]
        student = frappe.get_doc("Student", {"reference_number": student_ref_id})
        data = {
            **student.as_dict(),
            **student_data
        }
        notice_subject = render_jinja(subject, data)
        notice_content = render_jinja(content, data)

    test_emails = [e.strip() for e in str(test_emails).split(",")]
    return create_email(
        recipients=test_emails,
        subject=notice_subject,
        content=notice_content,
        send_email=True,
        read_receipt=True,
    )
