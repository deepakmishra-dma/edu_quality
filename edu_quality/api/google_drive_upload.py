import frappe
from edu_quality.api.google_service_auth import GoogleServiceAccountAuth
from googleapiclient.discovery import build
from requests import get, post
from googleapiclient.errors import HttpError
import os
from urllib.parse import quote
import tempfile

from apiclient.http import MediaFileUpload


@frappe.whitelist()
def get_google_drive_object():
    """
    Returns an object of Google Drive.
    """

    oauth_obj = GoogleServiceAccountAuth("drive")

    google_drive = oauth_obj.get_google_service_object()

    return google_drive


def get_google_folder_name_with_id(folder_id):
    try:
        if not folder_id:
            return False
        folder_exist = (
            get_google_drive_object()
            .files()
            .get(fileId=folder_id, fields="name")
            .execute()
        )
        return folder_exist
    except Exception as e:
        if e.resp.status == 404:
            return False
        frappe.msgprint("Something Went Wrong")
        return False


def check_for_folder_in_google_drive(folder_name=None, root_folder=None):
    """Checks if folder exists in Google Drive else create it."""
    service_account_doc = frappe.get_single("Google Service Account")
    root_folder_id = root_folder or service_account_doc.get(("root_folder"))

    if folder_name == None:
        return root_folder_id

    def _create_folder_in_google_drive(google_drive, folder_name):
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [root_folder_id],
        }

        try:
            folder = (
                google_drive.files()
                .create(body=file_metadata, fields="id")
                .execute()
                .get("id")
            )
            backup_folder_exists = True
            return folder

        except HttpError as e:
            frappe.throw(
                (
                    "Google Drive - Could not create folder in Google Drive - Error Code {0}"
                ).format(e)
            )

    google_drive = get_google_drive_object()

    try:
        google_drive_folders = (
            google_drive.files()
            .list(
                q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{root_folder_id}' in parents"
            )
            .execute()
        )

    except HttpError as e:
        frappe.throw(
            (
                "Google Drive - Could not find folder in Google Drive - Error Code {0}"
            ).format(e)
        )
    backup_folder_exists = False
    for f in google_drive_folders.get("files"):
        if f.get("name") == folder_name:
            backup_folder_exists = True
            return f.get("id")
    if not backup_folder_exists:
        return _create_folder_in_google_drive(google_drive, folder_name)


def get_absolute_path(file_url):
    site_path = frappe.get_site_path()
    if "private" in file_url:
        file_path = site_path + file_url
    else:
        file_path = site_path + "/public" + file_url
    return file_path


@frappe.whitelist()
def upload_file_to_drive(file_url, folder_name, root_folder=None):
    # Get Google Drive Object
    google_drive = get_google_drive_object()

    # Check if folder exists in Google Drive
    id = check_for_folder_in_google_drive(folder_name, root_folder)

    file_metadata = {"name": os.path.basename(file_url), "parents": [id]}

    try:
        media = MediaFileUpload(
            get_absolute_path(file_url), mimetype="image/jpeg", resumable=True
        )
        google_drive.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
    except OSError as e:
        frappe.throw(("Google Drive - Could not locate - {0}").format(e))

    return "Google Drive Backup Successful."


def upload_file_stream_to_drive(file_content, root_folder, file_name, mimetype):
    # Get Google Drive Object

    google_drive = get_google_drive_object()
    id = check_for_folder_in_google_drive(None, root_folder)
    file_metadata = {"name": file_name, "parents": [id]}

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_content)
    temp_file.close()

    try:
        media = MediaFileUpload(temp_file.name, mimetype=mimetype, resumable=True)
        result = (
            google_drive.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        return result

    except Exception as e:
        frappe.throw(("Google Drive - Could not locate - {0}").format(e))
    finally:
        if os and temp_file and temp_file.name:
            os.remove(temp_file.name)
    return "Google Drive File Upload Successful"


def find_file_by_name_and_folder(file_name, root_folder_id):
    try:
        if not root_folder_id or not file_name:
            return False
        google_drive = get_google_drive_object()
        query = f"name='{file_name}' and '{root_folder_id}' in parents"

        results = google_drive.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])

        if files:
            return files[0]
        else:
            print("No files found with that name.")
            return False
    except Exception as e:
        return False


def update_file_stream_on_drive(file_content, file_id, mimetype):
    # Get Google Drive Object

    google_drive = get_google_drive_object()
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_content)
    temp_file.close()

    try:
        media = MediaFileUpload(temp_file.name, mimetype=mimetype, resumable=True)
        result = (
            google_drive.files()
            .update(fileId=file_id, media_body=media, fields="id")
            .execute()
        )
        return result

    except Exception as e:
        frappe.throw(("Google Drive - Could not locate - {0}").format(e))
    finally:

        os.remove(temp_file.name)
    return "Google Drive File Update Successful"


# edu_quality.edu_quality.api.google_drive_upload.upload_file
@frappe.whitelist()
def upload_file(file_url, folder_name, root_folder=None):
    frappe.enqueue(
        "edu_quality.api.google_drive_upload.upload_file_to_drive",
        queue="long",
        timeout=1800,
        file_url=file_url,
        folder_name=folder_name,
        root_folder=root_folder,
    )
    return "Queued Successfully"
