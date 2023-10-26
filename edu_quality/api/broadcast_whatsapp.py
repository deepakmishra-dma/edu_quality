import frappe


# edu_quality.api.broadcast_whatsapp.message
@frappe.whitelist()
def message(**data):
    members = data.get("members")
    message = data.get("message")
    if not members or not message:
        return

    for i in members:
        send(i.get("member_name"), message)
    return data


def send(member_lead_id, message):
    lead_doc = frappe.get_doc("Lead", member_lead_id)
    contact_doc_name = frappe.db.get_value(
        "Contact",
        {
            "first_name": lead_doc.first_name,
            "last_name": lead_doc.last_name,
            "email_id": lead_doc.fathers_email,
            "mobile_no": lead_doc.fathers_phone,
        },
        "name",
    )
    message["to"] = contact_doc_name
    message["doctype"] = "WhatsApp Message"
    message_doc = frappe.get_doc(message)
    message_doc.insert()
    message_doc.upload_media()
    message_doc.send_templated_message()
