import frappe
from edu_quality.api.google_service_auth import GoogleServiceAccountAuth
from googleapiclient.discovery import build
from requests import get, post
from googleapiclient.errors import HttpError
import os
import secrets
from edu_quality.public.py.utils import add_indian_country_code
import re


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


@frappe.whitelist()
def get_google_user_with_key(email_key):
    admin_obj = get_google_admin_object()
    return (
        admin_obj.users()
        .get(
            userKey=f"{email_key}@walnutedu.in",
        )
        .execute()
    )


@frappe.whitelist()
def create_google_user(
    email_key, first_name, last_name, recovery_mail, phone_no, school
):
    user_service = get_google_admin_object()
    exception = False
    existing_user = None
    try:
        existing_user = (
            user_service.users()
            .get(
                userKey=f"{email_key}@walnutedu.in",
            )
            .execute()
        )
        frappe.log_error("Account get for  ", str(existing_user))
    except:
        frappe.log_error("Correct exception")
        exception = True

    try:
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
                "orgUnitPath": f"/{school}/Students",
            }

            if recovery_mail:
                recovery_mail = (str(recovery_mail) or "feedback@walnutedu.in").strip().lower()
                # only matches lower case emails
                email_pattern = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
                match = re.match(email_pattern, recovery_mail)
                if not match:
                    recovery_mail = "feedback@walnutedu.in"
                new_user["recoveryEmail"] = recovery_mail

            if phone_no:
                new_user["recoveryPhone"] = add_indian_country_code(phone_no, True)
            frappe.log_error("account creating for ", str(new_user))
            resp = (
                user_service.users()
                .insert(
                    body=new_user,
                )
                .execute()
            )
            frappe.log_error("Account created for ", str(resp))
            return resp
    except Exception as e:
        frappe.log_error(
            "Google Account Creation failed",
            str(
                [
                    frappe.get_traceback(),
                    "variables",
                    email_key,
                    first_name,
                    last_name,
                    recovery_mail,
                    phone_no,
                    school,
                ]
            ),
        )
    # frappe.log_error("google account created with" + str(existing_user))
    return existing_user


def add_user_to_group(email, group_email):
    try:
        user_service = get_google_admin_object()
        user_service.members().insert(
            groupKey=group_email, body={"email": email, "role": "MEMBER"}
        ).execute()
    except Exception as e:
        frappe.logger("google_groups").exception(e)


def remove_user_from_group(email, group_email):
    try:
        user_service = get_google_admin_object()
        user_service.members().delete(groupKey=group_email, memberKey=email)
    except Exception as e:
        frappe.logger("google_groups").exception(e)


def suspend_google_user(email):
    user_service = get_google_admin_object()
    user_service.users().update(
        userKey=email,
        body={"suspended": True},
    ).execute()


def unsuspend_google_user(email):
    user_service = get_google_admin_object()
    user_service.users().update(
        userKey=email,
        body={"suspended": False},
    ).execute()
