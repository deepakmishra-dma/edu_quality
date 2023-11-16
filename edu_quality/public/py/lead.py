import frappe

from edu_quality.public.py.utils import add_indian_country_code
try:
    from nextai.funnel.custom_trigger import trigger_event
except ImportError:
    print("Chatnext is not installed")


def after_insert(doc, method=None):
    doc.contact_doc.whatsapp_id = add_indian_country_code(doc.fathers_phone)
    if doc.fathers_phone:
        doc.contact_doc.append(
            "phone_nos", {"phone": doc.fathers_phone, "is_primary_mobile_no": 1}
        )

    if doc.fathers_email:
        doc.contact_doc.append(
            "email_ids", {"email_id": doc.fathers_email, "is_primary": 1}
        )

    doc.contact_doc.save()
    if doc.get("fathers_email"):
        content = enqueue_email(doc)
        if content:
            add_email_activity(doc, content)

    try:
        trigger_event(doc, "lead_created")
    except Exception as e:
        frappe.log_error("Error triggering lead_created event", str(e))
    pass


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
