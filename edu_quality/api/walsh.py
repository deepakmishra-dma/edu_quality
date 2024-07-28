import frappe
from edu_quality.public.py.utils import sms_otp

@frappe.whitelist(allow_guest=True)
def get_otp(phone_number):
    sms_otp(7976865251,1234)
    return

@frappe.whitelist(allow_guest=True)
def login(otp,phone_number):
    l

    