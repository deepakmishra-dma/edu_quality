import frappe
from edu_quality.api.google_service_auth import GoogleServiceAccountAuth
from googleapiclient.discovery import build
from requests import get, post
from googleapiclient.errors import HttpError
import os
import secrets

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



def create_google_user(school_code, refno, first_name, last_name, recovery_mail):
    user_service = get_google_admin_object()
    print(user_service)
    new_user = {
        "primaryEmail": f"{school_code}-{refno}@walnutedu.in",
        "name": {
            "givenName": first_name,
            "familyName": last_name,
        },
        "password": "walnut@12345",
        "changePasswordAtNextLogin": True,
        "ipWhitelisted": False,
        "recoveryEmail": recovery_mail,
        "orgUnitPath": f"/Walnut School at Wakad/Students",
        # "domain": "walnutedu.in",
        # "kind": "admin#directory#user",
    }
    # result = (
    #     user_service.users()
    #     .get(userKey="shbb04-demo@walnutedu.in", domain="walnutedu.in")
    #     .execute()
    # )
    # print(result["primaryEmail"], result["name"]["fullName"])
    # result = user_service.users().list(domain="walnutedu.in").execute()
    # users = result.get("users", [])
    # return users
    return (
        user_service.users()
        .insert(
            body=new_user,
        )
        .execute()
    )
