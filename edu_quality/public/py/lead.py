import frappe

from edu_quality.public.py.utils import add_indian_country_code


def before_insert(doc, method=None):
    contacts = frappe.db.get_list(
        "Contact",
        {"whatsapp_id": add_indian_country_code(doc.fathers_phone)},
        limit_page_length=1,
        order_by="creation desc",
        ignore_permissions=True,
    )

    if len(contacts):
        doc.contact_doc = frappe.get_doc(
            "Contact", contacts[0], ignore_permissions=True
        )
    else:
        doc.contact_doc = doc.create_contact()
    doc.custom_contact_link = doc.contact_doc.get("name")
    doc.contact_doc.flags.ignore_permissions = True


def after_insert(doc, method=None):
    if not doc.contact_doc:
        return
    doc.contact_doc.whatsapp_id = add_indian_country_code(doc.fathers_phone)
    if len(doc.contact_doc.phone_nos) == 0:
        if doc.fathers_phone:
            doc.contact_doc.append(
                "phone_nos",
                {
                    "phone": doc.fathers_phone,
                    "is_primary_mobile_no": 1,
                },
            )
    if len(doc.contact_doc.email_ids) == 0:
        if doc.fathers_email:
            doc.contact_doc.append(
                "email_ids",
                {
                    "email_id": doc.fathers_email,
                    "is_primary": 1,
                },
            )

    doc.contact_doc.save(ignore_permissions=True)
    if doc.get("fathers_email"):
        content = enqueue_email(doc)
        if content:
            add_email_activity(doc, content)


def enqueue_email(doc):
    try:
        email = doc.get("fathers_email")
        program = doc.get("class")
        template_name = frappe.db.get_value("Program", program, "custom_email_template")
        email_template = frappe.get_doc("Email Template", template_name)

        content = frappe.render_template(
            email_template.get("response_html") or email_template.get("response"), {}
        )
        send_unsubscribe_message = frappe.get_value(
            "Email Account", {"default_outgoing": 1}, "send_unsubscribe_message"
        )
        email_args = {
            "recipients": [email],
            "subject": email_template.get("subject"),
            "message": content,
            "reference_doctype": doc.get("doctype"),
            "reference_name": doc.get("name"),
            "add_unsubscribe_link": send_unsubscribe_message,
            "unsubscribe_message": frappe._("Click Here"),
            "delayed": False,
        }

        frappe.sendmail(**email_args)
        return content
    except Exception as e:
        frappe.log_error("Error sending lead generation email", str(e))
        return None


def add_email_activity(doc, content):
    frappe.get_doc(
        {
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "subject": "Lead Generation",
            "content": content,
            "sent_or_received": "Sent",
            "sender": frappe.session.user,
            "recipients": doc.get("fathers_email"),
            "reference_doctype": "Lead",
            "reference_name": doc.get("name"),
        }
    ).insert(ignore_permissions=True)
