import frappe
from edu_quality.api.google_service_auth import GoogleServiceAccountAuth
from googleapiclient.discovery import build
from requests import get, post
from googleapiclient.errors import HttpError
import os
from urllib.parse import quote

from apiclient.http import MediaFileUpload

@frappe.whitelist()
def get_google_drive_object():
	"""
	Returns an object of Google Drive.
	"""

	oauth_obj = GoogleServiceAccountAuth("drive")

	google_drive = oauth_obj.get_google_service_object()

	return google_drive

def check_for_folder_in_google_drive(folder_name):
	"""Checks if folder exists in Google Drive else create it."""

	def _create_folder_in_google_drive(google_drive, folder_name):
		service_account_doc = frappe.get_single('Google Service Account')

		file_metadata = {
			"name": folder_name,
			"mimeType": "application/vnd.google-apps.folder",
			"parents":[service_account_doc.get('root_folder')]
		}
		
		try:
			folder = google_drive.files().create(body=file_metadata, fields="id").execute().get("id")
			backup_folder_exists=True
			return folder
			
		except HttpError as e:
			frappe.throw(
				("Google Drive - Could not create folder in Google Drive - Error Code {0}").format(e)
			)

	google_drive = get_google_drive_object()

	try:
		service_account_doc = frappe.get_single('Google Service Account')
		google_drive_folders = (
			google_drive.files().list(q=f"mimeType='application/vnd.google-apps.folder' and '{service_account_doc.get('root_folder')}' in parents").execute()
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
	google_drive = get_google_drive_object()

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

# edu_quality.edu_quality.api.google_drive_upload.upload_file	
@frappe.whitelist()
def upload_file(file_url,folder_name):
	frappe.enqueue(
		"edu_quality.api.google_drive_upload.upload_file_to_drive",
        queue="long",
		timeout=1800,
		file_url= file_url,
		folder_name=folder_name
	)
	return 'Queued Successfully'