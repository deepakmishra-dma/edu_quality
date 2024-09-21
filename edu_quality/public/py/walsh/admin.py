import csv
import json

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

    if len(failure_ref_ids):
        frappe.get_doc({
            'doctype': 'School Notice Error',
            'type': 'notice',
            'failure_list': json.dumps(failure_ref_ids, default=str, indent=2),
            'failure_messages': json.dumps(failure_texts, default=str, indent=2)
        }).insert(ignore_permissions=True)


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
    school_admin_bcc_email = ""
    for row in csv_data:
        try:
            student_ref_id = row["student_ref_id"]
            student = frappe.get_doc("Student", {"reference_number": student_ref_id})
            if not school_admin_bcc_email:
                school = frappe.get_doc("School", student.school)
                school_admin_bcc_email = school.bcc_email_address
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
                bcc=bcc_emails + ([school_admin_bcc_email] if school_admin_bcc_email else []),
                send_email=True,
                read_receipt=True,
            )
            bcc_emails = []
            success_ref_ids.append(student_ref_id)
        except Exception as e:
            failure_ref_ids.append(row.get("student_ref_id"))
            failure_texts.append(e)

    if len(failure_ref_ids):
        frappe.get_doc({
            'doctype': 'School Notice Error',
            'type': 'email',
            'failure_list': json.dumps(failure_ref_ids, default=str, indent=2),
            'failure_messages': json.dumps(failure_texts, default=str, indent=2)
        }).insert(ignore_permissions=True)


def enqueued_generic_notice_emails(__args):
    subject = __args.get("subject")
    content = __args.get("notice")
    bcc_email_groups = __args.get("bcc_email_groups")
    classes = __args.get("classes")
    divisions = __args.get("divisions")
    student_statuses = __args.get("student_statuses")

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

    students = []
    if len(classes) > 1:
        students_values = {'classes': classes, 'student_statuses': student_statuses}
        students = frappe.db.sql('''
            select *
            from tabStudent
            where name in (
               select student
               from `tabProgram Enrollment`
               where program in %(classes)s
            )
            and student_status in %(student_statuses)s
        ''', values=students_values, as_dict=1)
    else:
        students_values = {'divisions': divisions, 'student_statuses': student_statuses}
        students = frappe.db.sql('''
            select *
            from tabStudent
            where name in (
               select student
               from `tabProgram Enrollment`
               where student_group in %(divisions)s
            )
            and student_status in %(student_statuses)s
        ''', values=students_values, as_dict=1)

    success_ref_ids = []
    failure_ref_ids = []
    failure_texts = []
    school_admin_bcc_email = ""
    for student in students:
        try:
            notice_subject = render_jinja(subject, student)
            notice_content = render_jinja(content, student)
            student_email = student.student_email_id
            if not school_admin_bcc_email:
                school = frappe.get_doc("School", student.school)
                school_admin_bcc_email = school.bcc_email_address
            create_email(
                recipients=[student_email],
                subject=notice_subject,
                content=notice_content,
                bcc=bcc_emails + ([school_admin_bcc_email] if school_admin_bcc_email else []),
                send_email=True,
                read_receipt=True,
            )
            bcc_emails = []
            success_ref_ids.append(student.student_ref_id)
        except Exception as e:
            failure_ref_ids.append(student.get("student_ref_id"))
            failure_texts.append(e)

    if len(failure_ref_ids):
        frappe.get_doc({
            'doctype': 'School Notice Error',
            'type': 'email',
            'failure_list': json.dumps(failure_ref_ids, default=str, indent=2),
            'failure_messages': json.dumps(failure_texts, default=str, indent=2)
        }).insert(ignore_permissions=True)


def enqueued_generic_notice_docs(__args):
    subject = __args.get("subject")
    content = __args.get("notice")
    school = __args.get("school")
    classes = __args.get("classes")
    divisions = __args.get("divisions")
    student_statuses = __args.get("student_statuses")

    for student_status in student_statuses:
        if len(classes) > 1 or len(divisions) == 0:
            for class_ in classes:
                frappe.get_doc({
                    "doctype": "School Notice",
                    "class": class_,
                    "is_generic_notice": 1,
                    "school": school,
                    "subject": subject,
                    "student_status": student_status,
                    "notice": content
                }).insert()
        else:
            class_ = classes[0]
            for division in divisions:
                frappe.get_doc({
                    "doctype": "School Notice",
                    "is_generic_notice": 1,
                    "class": class_,
                    "school": school,
                    "division": division,
                    "subject": subject,
                    "student_status": student_status,
                    "notice": content
                }).insert()


def validate_args(**kwargs):
    has_csv = kwargs.get("has_csv")
    csv_file = kwargs.get("csv_file")
    subject = kwargs.get("subject")
    content = kwargs.get("notice")
    send_emails = kwargs.get("send_emails")
    bcc_email_groups = kwargs.get("bcc_email_groups")
    school = kwargs.get("school")
    classes = kwargs.get("classes")
    divisions = kwargs.get("divisions")
    student_statuses = kwargs.get("student_statuses")
    is_test = kwargs.get("is_test")

    # verify supplied data
    if has_csv and not is_test:
        csv_text = frappe.get_doc("File", {
            "file_url": csv_file,
        }, limit=1).get_content()

        if not csv_text:
            raise frappe.exceptions.ValidationError("CSV File not found")
    else:
        if not school:
            raise frappe.exceptions.MandatoryError("School is required")

        if not classes:
            raise frappe.exceptions.MandatoryError("Classes are required")
        if not isinstance(classes, list):
            raise frappe.exceptions.ValidationError("Classes must be a list")
        if not len(classes):
            raise frappe.exceptions.MandatoryError("At least one Class is required")

        if len(classes) == 1 and divisions:
            if not isinstance(divisions, list):
                raise frappe.exceptions.ValidationError("Divisions must be a list")

        if not student_statuses:
            raise frappe.exceptions.MandatoryError("Student Statuses are required")
        if not isinstance(student_statuses, list):
            raise frappe.exceptions.ValidationError("Student Statuses must be a list")
        if not len(student_statuses):
            raise frappe.exceptions.MandatoryError("At least one Student Status is required")

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


@frappe.whitelist()
def create_notice(**kwargs):
    has_csv = kwargs.get("has_csv")
    send_emails = kwargs.get("send_emails")

    # verify supplied data
    validate_args(**kwargs)

    if has_csv:
        frappe.enqueue(enqueued_specific_notice_docs, __args=kwargs)
        if send_emails:
            frappe.enqueue(enqueued_specific_notice_emails, queue="long", __args=kwargs)
    else:
        frappe.enqueue(enqueued_generic_notice_docs, __args=kwargs)
        if send_emails:
            frappe.enqueue(enqueued_generic_notice_emails, queue="long", __args=kwargs)


@frappe.whitelist()
def send_test_mail(**kwargs):
    has_csv = kwargs.get("has_csv")
    student_data = kwargs.get("student_data")
    subject = kwargs.get("subject")
    content = kwargs.get("notice")
    test_emails = kwargs.get("emails")
    classes = kwargs.get("classes")
    divisions = kwargs.get("divisions")
    student_statuses = kwargs.get("student_statuses")
    if not test_emails:
        raise frappe.exceptions.MandatoryError("Test Emails are required")

    validate_args(**kwargs, is_test=True)

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

    students = []
    if len(classes) > 1:
        students_values = {'classes': classes, 'student_statuses': student_statuses}
        students = frappe.db.sql('''
            select *
            from tabStudent
            where name in (
               select student
               from `tabProgram Enrollment`
               where program in %(classes)s
            )
            and student_status in %(student_statuses)s
            limit 1
        ''', values=students_values, as_dict=1)
    else:
        students_values = {'divisions': divisions, 'student_statuses': student_statuses}
        students = frappe.db.sql('''
            select *
            from tabStudent
            where name in (
               select student
               from `tabProgram Enrollment`
               where student_group in %(divisions)s
            )
            and student_status in %(student_statuses)s
            limit 1
        ''', values=students_values, as_dict=1)

    if len(students):
        notice_subject = render_jinja(subject, students[0])
        notice_content = render_jinja(content, students[0])

    test_emails = [e.strip() for e in str(test_emails).split(",")]
    return create_email(
        recipients=test_emails,
        subject=notice_subject,
        content=notice_content,
        send_email=True,
        read_receipt=True,
    )
