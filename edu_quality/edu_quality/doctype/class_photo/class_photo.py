# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from edu_quality.api.google_drive_upload import upload_file
from frappe.model.document import Document


class ClassPhoto(Document):
    pass


@frappe.whitelist()
def move_existing_and_upload_to_drive(**data):
    folder_name = data.get("storedParams").get("folder_name")
    # existing_folder = frappe.db.exists("File", {"name": f"Home/{folder_name}"})
    service_account_doc = frappe.get_single("Google Service Account")
    file_doc = frappe.get_doc("File", data.get("name"))
    upload_file(
        file_doc.file_url, folder_name, service_account_doc.get("class_photo_folder")
    )
    file_doc.folder = f"Home/{folder_name}"
    file_doc.save()
    return "SUCCESS"
