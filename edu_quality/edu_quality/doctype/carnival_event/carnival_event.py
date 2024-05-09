# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from edu_quality.api.google_drive_upload import upload_file
from frappe.model.document import Document


class CarnivalEvent(Document):
    pass


@frappe.whitelist()
def move_existing_and_upload_to_drive(**data):
    file_doc = frappe.get_doc("File", data.get("name"))
    upload_file(file_doc.file_url, data.get("name"))
    file_doc.folder = f"Home/{data.get('storedParams').get('folder_name')}"
    file_doc.save()
    return "SUCCESS"
