# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from edu_quality.public.py.walsh.admin import notification_sender


class AttendanceEntry(Document):

    def on_update(self):
        self.send_email_to_admins()
        self.assign_doc_to_admins()
        self.send_notification_to_councellor()

    def send_email_to_admins(self):
        try:
            from nextai.funnel.custom_trigger import trigger_event

            trigger_event(doc=self, event_name="attendance_entry_created")
        except Exception as e:
            print("Chatnext is not installed")

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

    def send_notification_to_councellor(self):
        try:
            class_attr = getattr(self, "class")
            school = frappe.get_value("Program", class_attr, "school")
            subject = "Attendance Entry for Early Pickup - " + self.student

            users = frappe.get_all(
                "User Permission",
                {"allow": "School", "for_value": school},
                pluck="user",
            )
            users = list(filter(check_councellor_role, users))
            url_path = f"/attendance-entry/{self.name}"
            for user in users:
                notification_sender(
                    user, self.student, subject=subject, url_path=url_path
                )
        except:
            frappe.log_error(
                "Error Sending Notification to Councellor", frappe.get_traceback()
            )


def check_councellor_role(user):
    roles = frappe.get_roles(user)
    return "Councellor" in roles
