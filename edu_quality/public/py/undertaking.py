import frappe
import math, random
from edu_quality.public.py.utils import verify_otp


@frappe.whitelist()
def generate_undertaking_otp(payment_hash):
    fee = get_fee(payment_hash)
    return generate_otp(fee)


@frappe.whitelist()
def verify_undertaking_otp(payment_hash, otp):
    fee = get_fee(payment_hash)
    return verify_otp(fee, otp)


def get_fee(payment_hash):
    fee = frappe.get_value(
        "Payment Request", {"payment_hash": payment_hash}, "reference_name"
    )
    return fee


def generate_otp(fee):
    try:
        rs = frappe.cache()
        key = fee
        digits = "0123456789"
        OTP = ""
        for i in range(4):
            OTP += digits[math.floor(random.random() * 10)]
        rs.set_value(key, OTP, expires_in_sec=300)
        return send_otp(fee, OTP)
    except Exception as e:
        return False


def send_otp(fee, otp):
    try:
        student = frappe.get_value("Fees", fee, "student")
        student = frappe.get_doc("Student", student)
        if student.custom_fathers_email:
            email = student.custom_fathers_email
        elif student.custom_mothers_email:
            email = student.custom_mothers_email
        elif student.custom_guardians_email_id:
            email = student.custom_guardians_email_id
        elif student.student_email_id:
            email = student.student_email_id
        if email:
            email_otp(email, otp)
        # whatsapp message
        return True
    except Exception as e:
        return False


def email_otp(email, otp):
    subject = "OTP for Undertaking Submission"
    message = f"OTP for Undertaking Submission is {otp}"
    frappe.sendmail(recipients=email, subject=subject, message=message, delayed=False)
