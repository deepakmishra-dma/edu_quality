import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
from requests import get, post
import frappe
from urllib.parse import quote
from apiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
import frappe.integrations.google_oauth as oauth


CALLBACK_METHOD = "/api/method/frappe.integrations.google_oauth.callback"
_SCOPES = {
    "mail": ("https://mail.google.com/"),
    "contacts": ("https://www.googleapis.com/auth/contacts"),
    "drive": ("https://www.googleapis.com/auth/drive"),
    "indexing": ("https://www.googleapis.com/auth/indexing"),
}
_SERVICES = {
    "contacts": ("people", "v1"),
    "drive": ("drive", "v3"),
    "indexing": ("indexing", "v3"),
}
_DOMAIN_CALLBACK_METHODS = {
    "mail": "frappe.email.oauth.authorize_google_access",
    "contacts": "frappe.integrations.doctype.google_contacts.google_contacts.authorize_access",
    "drive": "edu_quality.edu_quality.doctype.google_drive_settings.google_drive_settings.authorize_access",
    "indexing": "frappe.website.doctype.website_settings.google_indexing.authorize_access",
}


class GoogleServiceAccountAuth:
    def __init__(self, domain: str, validate: bool = True):
        self.google_settings = frappe.get_single("Google Service Account")

        self.domain = domain.lower()
        self.scopes = (
            " ".join(_SCOPES[self.domain])
            if isinstance(_SCOPES[self.domain], (list, tuple))
            else _SCOPES[self.domain]
        )

        if validate:
            self.validate_google_settings()

    def validate_google_settings(self):
        google_settings = "<a href='/app/google-settings'>Google Settings</a>"

        if not self.google_settings.service_account_credentials_json:
            frappe.throw(
                frappe._("Please enable {} before continuing.").format(google_settings)
            )

    def get_google_service_object(self):
        """Returns google service object"""

        credentials = service_account.Credentials.from_service_account_file(
            get_absolute_path(self.google_settings.service_account_credentials_json),
            scopes={self.scopes},
        )

        return build(
            serviceName=_SERVICES[self.domain][0],
            version=_SERVICES[self.domain][1],
            credentials=credentials,
            static_discovery=False,
        )


class CustomGoogleOAuth:
    pass


@frappe.whitelist(methods=["GET"])
def callback(state: str, code: str = None, error: str = None) -> None:
    """Common callback for google integrations.
    Invokes functions using `frappe.get_attr` and also adds required (keyworded) arguments
    along with committing and redirecting us back to frappe site."""

    state = json.loads(state)
    redirect = state.pop("redirect", "/app")
    success_query_param = state.pop("success_query_param", "")
    failure_query_param = state.pop("failure_query_param", "")

    if not error:
        if (domain := state.pop("domain")) in _DOMAIN_CALLBACK_METHODS:
            state.update({"code": code})
            frappe.get_attr(_DOMAIN_CALLBACK_METHODS[domain])(**state)

            # GET request, hence using commit to persist changes
            frappe.db.commit()  # nosemgrep
        else:
            return frappe.respond_as_web_page(
                "Invalid Google Callback",
                "The callback domain provided is not valid for Google Authentication",
                http_status_code=400,
                indicator_color="red",
                width=640,
            )

    frappe.local.response["type"] = "redirect"
    frappe.local.response[
        "location"
    ] = f"{redirect}?{failure_query_param if error else success_query_param}"


def get_absolute_path(file_url):
    site_path = frappe.get_site_path()
    if "private" in file_url:
        file_path = site_path + file_url
    else:
        file_path = site_path + "/public" + file_url
    return file_path
