import json
import random

import frappe
from frappe.auth import LoginManager
from nextai.whatsapp_business_api_integration.doctype.whatsapp_message.whatsapp_message import send_templated_message

from edu_quality.public.py.utils import remove_indian_country_code


def format_wa_phone_no(phone_no):
    if not phone_no:
        return False
    if phone_no.startswith("+"):
        phone_no = phone_no[1:]
    if len(phone_no) == 10:
        phone_no = "91" + phone_no

    # check if all characters are numeric
    if not phone_no.isdigit():
        return False
    return phone_no


def create_otp(wa_phone_no):
    otp = ""
    for _ in range(4):
        otp += str(random.randint(0, 9))
    cache = frappe.cache()
    key = "walsh_otp_" + wa_phone_no
    cache.set_value(key, otp, expires_in_sec=3600)  # 1 hour
    return otp


def match_otp(wa_phone_no, otp):
    cache = frappe.cache()
    key = "walsh_otp_" + wa_phone_no
    cache_otp = cache.get_value(key)
    # print(wa_phone_no, "otp", otp, "cache_otp", cache_otp)
    return otp == cache_otp


def create_or_get_contact(wa_phone_number, contact_name):
    if frappe.db.exists("Contact", {"whatsapp_id": wa_phone_number}):
        contact = frappe.get_last_doc("Contact", filters={"whatsapp_id": wa_phone_number})
    else:
        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": contact_name,
            "whatsapp_id": wa_phone_number,
        }).insert(ignore_permissions=True)
    return contact


def send_otp_to_whatsapp(wa_phone_no, otp):
    contact = create_or_get_contact(wa_phone_no, "walsh:" + str(wa_phone_no))
    template_data = [{"type": "text", "text": f"{otp}"}]
    send_templated_message(contact.name, "walsh_new_adm_login", json.dumps(template_data))


def save_push_notification_token(token, user_id=None):
    user_id = user_id or frappe.session.user
    has_token = frappe.db.exists("Mobile Push Token", {"token": token, "user_id": user_id})
    if not has_token:
        frappe.get_doc({
            "doctype": "Mobile Push Token",
            "token": token,
            "user_id": user_id
        }).insert(ignore_permissions=True)


def remove_push_notification_token(token=None):
    user_id = frappe.session.user
    has_token = frappe.db.exists("Mobile Push Token", {"token": token, "user_id": user_id}) \
        if token else frappe.db.exists("Mobile Push Token", {"user_id": user_id})
    if token and has_token:
        frappe.db.delete("Mobile Push Token", {"token": token, "user_id": user_id})
    elif not token and has_token:
        frappe.db.delete("Mobile Push Token", {"user_id": user_id})


@frappe.whitelist(allow_guest=True)
def send_otp(phone_no):
    wa_phone_no = format_wa_phone_no(phone_no)
    if not wa_phone_no:
        return {
            "error": True,
            "error_type": "invalid_phone_number",
            "error_message": "Invalid Phone Number"
        }

    phone_with_country_code = "+" + str(wa_phone_no)
    guardian_number = remove_indian_country_code(phone_with_country_code)

    if not frappe.db.exists("User", {"phone": guardian_number}):
        return {
            "error": True,
            "error_type": "user_not_found",
            "error_message": "User Not Found"
        }

    otp = create_otp(wa_phone_no)
    send_otp_to_whatsapp(wa_phone_no, otp)
    return {
        "success": True,
        "message": "Otp Sent To +" + str(wa_phone_no) + " on WhatsApp",
    }


@frappe.whitelist(allow_guest=True)
def verify_otp(otp, phone_no, push_token=None):
    wa_phone_no = format_wa_phone_no(phone_no)
    phone_with_country_code = "+" + wa_phone_no
    guardian_number = remove_indian_country_code(phone_with_country_code)

    if match_otp(wa_phone_no, otp):
        user = frappe.get_doc("User", {"phone": guardian_number})
        login_manager = LoginManager()
        login_manager.login_as(user.name)

        if push_token:
            save_push_notification_token(push_token, user.name)

        return {
            "success": True,
            "message": "Login Successful",
        }
    return {
        "error": True,
        "error_type": "invalid_otp",
        "error_message": "Invalid OTP"
    }


@frappe.whitelist()
def register_push_notice(**kwargs):
    token = kwargs.get("token")
    if not token:
        raise frappe.exceptions.MandatoryError("Push Token is required")
    save_push_notification_token(token)


@frappe.whitelist()
def logout(token=None):
    remove_push_notification_token(token)
    login_manager = LoginManager()
    login_manager.logout()
    return {
        "success": True,
        "message": "Logout Successful",
    }
