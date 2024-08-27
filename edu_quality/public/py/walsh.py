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
    cache.set_value(key, otp, expires_in_sec=600)
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


def get_guardian_from_phone(full_phone_no):
    guardian_number = remove_indian_country_code(full_phone_no)
    if frappe.db.exists("Guardian", {"mobile_number": guardian_number}):
        return frappe.get_doc("Guardian", {"mobile_number": guardian_number}, order_by="creation", limit=1)


def get_or_create_user(full_phone_no):
    # print("create or get user", full_phone_no)
    if frappe.db.exists("User", {"phone": full_phone_no}):
        return frappe.get_doc("User", {"phone": full_phone_no})

    guardian_number = remove_indian_country_code(full_phone_no)
    guardian = get_guardian_from_phone(guardian_number)

    # create user with guardian details
    user = frappe.get_doc({
        "doctype": "User",
        "first_name": guardian.first_name,
        "last_name": guardian.last_name,
        "email": guardian.email_address,
        "phone": full_phone_no
    })
    user.insert(ignore_permissions=True)
    return user


def check_user_exists(phone_no):
    # print("check exists", phone_no)
    if frappe.db.exists("User", {"phone": phone_no}):
        return True
    guardian_number = remove_indian_country_code(phone_no)
    if frappe.db.exists("User", {"phone": guardian_number}):
        return True
    return False


def check_guardian_exists(full_phone_no):
    # print("check_guardian_exists", full_phone_no)
    guardian_number = remove_indian_country_code(full_phone_no)
    if frappe.db.exists("Guardian", {"mobile_number": guardian_number}):
        return True
    return False


def get_guardian_mail_from_phone(phone_no):
    guardian_number = remove_indian_country_code(phone_no)
    if frappe.db.exists("Guardian", {"mobile_number": guardian_number}):
        return frappe.get_value("Guardian", {"mobile_number": guardian_number}, "email_address", order_by="creation")


def get_user_from_email(email_id):
    # print("get user from email", email_id)
    if frappe.db.exists("User", {"name": email_id}):
        return frappe.get_doc("User", {"name": email_id})


@frappe.whitelist(allow_guest=True)
def send_otp(phone_no):
    wa_phone_no = format_wa_phone_no(phone_no)
    if not wa_phone_no:
        return {
            "error": True,
            "error_type": "invalid_phone_number",
            "error_message": "Invalid Phone Number"
        }

    phone_with_country_code = "+" + wa_phone_no

    if not check_user_exists(phone_with_country_code):
        if not check_guardian_exists(phone_with_country_code):
            return {
                "error": True,
                "error_type": "guardian_not_found",
                "error_message": "Guardian Not Found"
            }

        guardian_mail = get_guardian_mail_from_phone(phone_with_country_code)
        if not guardian_mail:
            return {
                "error": True,
                "error_type": "guardian_email_id_missing",
                "error_message": "Guardian Email Id Not Found"
            }

        if get_user_from_email(guardian_mail):
            return {
                "error": True,
                "error_type": "duplicate_guardian_mail",
                "error_message": "Guardian Mail Id Already Used with Another User"
            }

    otp = create_otp(wa_phone_no)
    send_otp_to_whatsapp(wa_phone_no, otp)
    return {
        "success": True,
        "message": "Otp Sent To +" + wa_phone_no,
    }


@frappe.whitelist(allow_guest=True)
def verify_otp(otp, phone_no):
    wa_phone_no = format_wa_phone_no(phone_no)
    phone_with_country_code = "+" + wa_phone_no

    if match_otp(wa_phone_no, otp):
        user = get_or_create_user(phone_with_country_code)
        login_manager = LoginManager()
        login_manager.login_as(user.name)
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
def get_all_notices():
    return frappe.get_all("School Notice", fields=["type_of_notifications", "subject", "html"])
