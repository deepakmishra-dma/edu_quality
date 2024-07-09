# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from edu_quality.api.google_drive_upload import (
    upload_file,
    check_for_folder_in_google_drive,
)
from frappe.model.document import Document


class CarnivalEvent(Document):
    def on_update(self, method=None):
        check_for_folder_in_google_drive(self.name)



@frappe.whitelist()
def check_folder_in_drive(folder_name):
    check_for_folder_in_google_drive(folder_name, None)


@frappe.whitelist()
def move_existing_and_upload_to_drive(**data):
    folder_name = data.get("storedParams").get("folder_name")
    # existing_folder = frappe.db.exists("File", {"name": f"Home/{folder_name}"})
    file_doc = frappe.get_doc("File", data.get("name"))
    upload_file(file_doc.file_url, folder_name)
    file_doc.folder = f"Home/{folder_name}"
    file_doc.save()
    return "SUCCESS"
