import frappe
import math, random, json
from edu_quality.public.py.utils import sms_otp, verify_otp, get_email_id, get_mobile_number

try:
    from nextai.whatsapp_business_api_integration.doctype.whatsapp_message.whatsapp_message import (
        send_templated_message,
    )
except ImportError:
    print("Chatnext is not installed")


@frappe.whitelist(allow_guest=True)
def generate_undertaking_otp(payment_hash=None,fee=None):
    if fee:
        doctype = "Fees"
        docname = fee
    else:
        doctype, docname = get_fee(payment_hash)
    return generate_otp(doctype, docname)


@frappe.whitelist(allow_guest=True)
def verify_undertaking_otp(otp,payment_hash=None,fee=None):
    if fee:
        doctype = "Fees"
        docname = fee
    else:
        doctype, docname = get_fee(payment_hash)
    return verify_otp(docname, otp)



def get_fee(payment_hash):
    doctype, docname = frappe.get_value(
        "Payment Request", {"payment_hash": payment_hash}, ["reference_doctype", "reference_name"]
    )
    return doctype, docname


def generate_otp(doctype, docname):
    try:
        rs = frappe.cache()
        key = docname
        digits = "0123456789"
        OTP = ""
        for i in range(6):
            OTP += digits[math.floor(random.random() * 10)]
        rs.set_value(key, OTP, expires_in_sec=300)
        return send_otp(doctype, docname, OTP)
    except Exception as e:
        return False


def send_otp(doctype, docname, otp):
    try:
        if doctype == "Fees":
            student = frappe.get_value("Fees", docname, "student")
        elif doctype == "Fee Advance":
            student = frappe.get_value("Fee Advance", docname, "student")

        student = frappe.get_doc("Student", student)
        mobile = get_mobile_number(student)
        email = get_email_id(student)
        if mobile:
            sms_otp(mobile, otp)
            if frappe.db.exists("Contact", {"whatsapp_id": mobile}):
                contact = frappe.get_doc("Contact", {"whatsapp_id": mobile})
                whatsapp_otp(contact, otp)

        if email:
            email_otp(email, otp)

        return True
    except Exception as e:
        frappe.logger("OTP").exception(e)
        return False


def whatsapp_otp(contact, otp):
    try:
        template_data = [{"type": "text", "text": f"{otp}"}]
        send_templated_message(contact, "send_otp_undertaking", json.dumps(template_data))
        return True
    except Exception as e:
        return False


def email_otp(email, otp):
    subject = "OTP for Undertaking Submission"
    message = f"OTP for Undertaking Submission is {otp}"
    frappe.sendmail(recipients=email, subject=subject, message=message, delayed=False)
