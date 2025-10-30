# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, getdate
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assign_to
from edu_quality.public.py.walsh.admin import notification_sender


class AttendanceEntry(Document):

    def on_update(self):
        if self.is_early_pickup():
            self.send_email_to_admins()
            self.assign_doc_to_admins()
            self.send_notification_to_councellor()

    def is_early_pickup(self):
        today_date = getdate(today())
        timestamps = frappe.get_all("Absent and Delay", {"parent": self.name, "status": ['like', '%early%']}, pluck="timestamp")
        for timestamp in timestamps:
            if timestamp.date() >= today_date:
                return True
        return False

    def send_email_to_admins(self):
        """
        This function sends an email to the admin group when an attendance entry is created
        """
        try:
            from nextai.funnel.custom_trigger import trigger_event

            trigger_event(doc=self, event_name="early_pickup")
        except Exception as e:
            print("Chatnext is not installed")

    def assign_doc_to_admins(self):
        """
        This function assigns the document to the admin group email users present in the school
        """
        admin_emails = self.get_admin_emails()
        users = [email for email in admin_emails if frappe.db.exists("User", email)]

        users_to_assign = [
            email
            for email in users
            if not frappe.db.exists(
                "ToDo", {"allocated_to": email, "reference_name": self.name, "status": "Open"}
            )
        ]
        if users_to_assign:
            add_assign_to(
                args={
                    "assign_to": users_to_assign,
                    "doctype": self.doctype,
                    "name": self.name,
                },
               ignore_permissions=True,
            )


    def get_admin_emails(self):
        """
        Returns:
            list: List of email addresses of the admin group of the school
        """
        school = frappe.get_value("Program", getattr(self, "class"), "school")
        admin_group = frappe.get_value("School", school, "admin_group")
        return frappe.get_all(
            "Email Group Member",
            filters={"email_group": admin_group},
            pluck="email",
        )

    def send_notification_to_councellor(self):
        """
        This function sends a notification to the councellor of the school on Mobile App
        """
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
