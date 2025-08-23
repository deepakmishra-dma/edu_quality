# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AttendanceEntry(Document):

    def on_update(self):
        self.send_email_to_admins()
        self.assign_doc_to_admins()

    def send_email_to_admins(self):
        admin_emails = self.get_admin_emails()
        if admin_emails:
            timestamp = frappe.get_value(
                "Absent and Delay",
                {"parent": self.name, "status": "early_pickup"},
                "timestamp",
            )
            message = f"Attendance Entry has been created/updated for student {self.student_name}({self.student}) of class {getattr(self, 'class')} on {timestamp}"
            frappe.sendmail(
                recipients=admin_emails, subject="Attendance Entry", message=message
            )

    def assign_doc_to_admins(self):
        admin_emails = self.get_admin_emails()
        for email in admin_emails:
            user = frappe.get_value("User", email, "name")
            if not user:
                continue
            assignments = {
                "doctype": "ToDo",
                "description": f"Assignment for {self.doctype}: {self.name}",
                "reference_type": self.doctype,
                "reference_name": self.name,
                "allocated_to": user,
                "status": "Open",
                "priority": "Medium",
            }
            frappe.get_doc(assignments).insert()

    def get_admin_emails(self):
        school = frappe.get_value("Program", getattr(self, "class"), "school")
        admin_group = frappe.get_value("School", school, "admin_group")
        return frappe.get_all(
            "Email Group Member",
            filters={"email_group": admin_group},
            pluck="email",
        )
