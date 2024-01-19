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


def create_google_user(school_code, refno, first_name, last_name):
    user_service = get_google_admin_object()

    new_user = {
        "primaryEmail": f"{school_code}-{refno}@example.com",
        "name": {
            "givenName": first_name,
            "familyName": last_name,
        },
        "password": secrets.token_urlsafe(PASSWORD_LENGTH),
    }

    user_service.users().insert(body=new_user).execute()
