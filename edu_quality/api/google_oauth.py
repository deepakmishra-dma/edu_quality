import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from requests import get, post
import frappe

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



class CustomGoogleOAuth(oauth.GoogleOAuth):
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

oauth.callback = callback
oauth._DOMAIN_CALLBACK_METHODS = _DOMAIN_CALLBACK_METHODS
