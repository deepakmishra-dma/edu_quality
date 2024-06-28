import frappe
import math, random, json
from edu_quality.public.py.utils import sms_otp, verify_otp, get_email_id, get_mobile_number

try:
    from nextai.whatsapp_business_api_integration.doctype.whatsapp_message.whatsapp_message import (
        send_templated_message,
    )
    from nextai.funnel.custom_trigger import trigger_event
except ImportError:
    print("Chatnext is not installed")
    trigger_event = None


@frappe.whitelist(allow_guest=True)
def generate_undertaking_otp(payment_hash=None, fee=None, fee_advance=None):
    if not trigger_event:
        return False
    doctype, docname = ("Fees", fee) if fee else ("Fee Advance", fee_advance) if fee_advance else get_fee(payment_hash)
    # fee_doc = frappe.get_doc(doctype, docname)
    # trigger_event(doc=fee_doc, event_name="undertaking_otp")
    from edu_quality.public.py.utils import generate_otp
    generate_otp(docname,undertaking=1)

    # generate_otp({"doc": fee_doc})
    return True


@frappe.whitelist(allow_guest=True)
def verify_undertaking_otp(otp, payment_hash=None, fee=None, fee_advance=None):
    doctype, docname = (fee and ("Fees", fee)) or (fee_advance and ("Fee Advance", fee_advance)) or get_fee(payment_hash)
    return verify_otp(docname, otp)



def get_fee(payment_hash):
    doctype, docname = frappe.get_value(
        "Payment Request", {"payment_hash": payment_hash}, ["reference_doctype", "reference_name"]
    )
    return doctype, docname


def generate_otp(variables):
    doc = variables.get("doc")
    rs = frappe.cache()
    key = doc.name
    OTP = ""
    for i in range(4):
        OTP += str(random.randint(1, 9))
    rs.set_value(key, OTP, expires_in_sec=600)

    variables["otp"] = OTP
    return send_otp(doc.doctype,doc.name, OTP)

def send_otp(doctype, docname, otp):
    try:
        if doctype == "Fees":
            student = frappe.get_value("Fees", docname, "student")
        elif doctype == "Fee Advance":
            student = frappe.get_value("Fee Advance", docname, "student")

        student = frappe.get_doc("Student", student)
        mobile = get_mobile_number(student)
        # email = get_email_id(student)
        if mobile:
            sms_otp(mobile, otp)
            if frappe.db.exists("Contact", {"whatsapp_id": mobile}):
                contact = frappe.get_doc("Contact", {"whatsapp_id": mobile})
                whatsapp_otp(contact, otp)

        # if email:
        #     email_otp(email, otp)

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
