# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from edu_quality.api.google_oauth import CustomGoogleOAuth as GoogleOAuth
from frappe.model.document import Document
from urllib.parse import quote
from apiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os


class GoogleDriveSettings(Document):
	def get_access_token(self):
		if not self.refresh_token:
			button_label = frappe.bold(("Allow Google Drive Access"))
			raise frappe.ValidationError(("Click on {0} to generate Refresh Token.").format(button_label))
		oauth_obj = GoogleOAuth("drive")
		r = oauth_obj.refresh_access_token(
			self.get_password(fieldname="refresh_token", raise_exception=False)
		)

		return r.get("access_token")

# edu_quality.edu_quality.doctype.google_drive_settings.google_drive_settings.authorize_access
@frappe.whitelist(methods=["POST"])
def authorize_access(reauthorize=False, code=None):

	oauth_code = (
		frappe.db.get_single_value("Google Drive Settings", "auth_code") if not code else code
	)
	oauth_obj = GoogleOAuth("drive")

	if not oauth_code or reauthorize:

		return oauth_obj.get_authentication_url(
			{
				"redirect": f"/app/Form/{quote('Google Drive Settings')}",
			},
		)

	r = oauth_obj.authorize(oauth_code)
	frappe.db.set_single_value(
		"Google Drive Settings",
		{"auth_code": oauth_code, "refresh_token": r.get("refresh_token")},
	)


def get_google_drive_object():
	"""
	Returns an object of Google Drive.
	"""
	account = frappe.get_doc("Google Drive Settings")
	oauth_obj = GoogleOAuth("drive")

	google_drive = oauth_obj.get_google_service_object(
		account.get_access_token(),
		account.get_password(fieldname="indexing_refresh_token", raise_exception=False),
	)

	return google_drive, account

def check_for_folder_in_google_drive(folder_name):
	"""Checks if folder exists in Google Drive else create it."""

	def _create_folder_in_google_drive(google_drive, folder_name):
		file_metadata = {
			"name": folder_name,
			"mimeType": "application/vnd.google-apps.folder",
		}

		try:
			folder = google_drive.files().create(body=file_metadata, fields="id").execute().get("id")
			backup_folder_exists=True
			return folder
			
		except HttpError as e:
			frappe.throw(
				("Google Drive - Could not create folder in Google Drive - Error Code {0}").format(e)
			)

	google_drive, account = get_google_drive_object()

	try:
		google_drive_folders = (
			google_drive.files().list(q="mimeType='application/vnd.google-apps.folder'").execute()
		)
		
	
	except HttpError as e:
		frappe.throw(
			("Google Drive - Could not find folder in Google Drive - Error Code {0}").format(e)
		)
	backup_folder_exists = False
	for f in google_drive_folders.get("files"):
		if f.get("name") == folder_name:
			frappe.db.commit()
			backup_folder_exists=True
			return f.get("id")
	if not backup_folder_exists:
		return	_create_folder_in_google_drive(google_drive, folder_name)

def get_absolute_path(file_url):
	site_path = frappe.get_site_path()
	if "private" in file_url:
		file_path = site_path + file_url
	else:
		file_path = site_path + "/public" + file_url
	return file_path

@frappe.whitelist()
def upload_file_to_drive(file_url,folder_name):

	# Get Google Drive Object
	google_drive, account = get_google_drive_object()

	# Check if folder exists in Google Drive
	id = check_for_folder_in_google_drive(folder_name)
	
	file_metadata = {"name": os.path.basename(file_url), "parents": [id]}

	try:
		media = MediaFileUpload(
			get_absolute_path(file_url), mimetype="image/jpeg", resumable=True
		)
		google_drive.files().create(body=file_metadata, media_body=media, fields="id").execute()
	except OSError as e:
		frappe.throw(("Google Drive - Could not locate - {0}").format(e))

	return ("Google Drive Backup Successful.")

# edu_quality.edu_quality.doctype.google_drive_settings.google_drive_settings.upload_file	
@frappe.whitelist()
def upload_file(file_url,folder_name):
	frappe.enqueue(
		"edu_quality.edu_quality.doctype.google_drive_settings.google_drive_settings.upload_file_to_drive",
        queue="long",
		timeout=1800,
		file_url= file_url,
		folder_name=folder_name
	)
	return 'Queued Successfully'

