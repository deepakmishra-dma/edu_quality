import frappe
import re


def add_indian_country_code(number):
    try:
        phone_pattern = r"^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$"
        is_91 = re.findall(phone_pattern, number)[0][0]

        if is_91:
            return number
        else:
            return "+91" + number

    except Exception as e:
        frappe.log_error("Error adding indian country code", str(e))
        return number


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
    pass
