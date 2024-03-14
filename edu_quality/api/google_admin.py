import frappe
from edu_quality.api.google_service_auth import GoogleServiceAccountAuth
from googleapiclient.discovery import build
from requests import get, post
from googleapiclient.errors import HttpError
import os
import secrets
from edu_quality.public.py.utils import add_indian_country_code

PASSWORD_LENGTH = 12


def get_google_admin_object():
    """
    Returns an object of Google Admin.
    """

    oauth_obj = GoogleServiceAccountAuth("admin")

    google_admin = oauth_obj.get_google_service_object()

    return google_admin


# edu_quality.api.google_admin.get_google_users
@frappe.whitelist()
def get_google_users():
    admin_obj = get_google_admin_object()
    return admin_obj.users().list()


def create_google_user(email_key, first_name, last_name, recovery_mail, phone_no):
    user_service = get_google_admin_object()
    exception = False
    try:
        existing_user = (
            user_service.users()
            .get(
                userKey=f"{email_key}@walnutedu.in",
            )
            .execute()
        )
    except:
        exception = True

    if exception:
        new_user = {
            "primaryEmail": f"{email_key}@walnutedu.in",
            "name": {
                "givenName": first_name,
                "familyName": last_name,
            },
            # "recoveryPhone": add_indian_country_code(phone_no, True),
            "password": "walnut@12345",
            "changePasswordAtNextLogin": True,
            "ipWhitelisted": False,
            # "recoveryEmail": recovery_mail,
            "orgUnitPath": f"/Walnut School at Wakad/Students",
        }
        if recovery_mail:
            new_user["recoveryEmail"] = recovery_mail

        if phone_no:
            new_user["recoveryPhone"] = add_indian_country_code(phone_no, True)

        return (
            user_service.users()
            .insert(
                body=new_user,
            )
            .execute()
        )
    frappe.log_error("google account created with" + str(existing_user))
    return existing_user
