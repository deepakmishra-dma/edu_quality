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
        admin_emails = self.get_admin_emails()
        if admin_emails:
            timestamp = frappe.get_value(
                "Absent and Delay",
                {"parent": self.name, "status": "early_pickup"},
                "timestamp",
            )
            message = f"Early Attendance Entry has been created/updated for student {self.student_name}({self.student}) of class {getattr(self, 'class')} on {timestamp}"
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

    def send_notification_to_councellor(self):
        try:
            academic_year = frappe.get_value(
                "Academic Year", {"custom_current_academic_year": 1}, "name"
            )
            class_attr = getattr(self, "class")
            school = frappe.get_value("Program", class_attr, "school")
            division = frappe.get_value(
                "Student Group Student", {"student": self.student}, "parent"
            )
            timestamp = frappe.get_value(
                "Absent and Delay",
                {"parent": self.name, "status": "early_pickup"},
                "timestamp",
            )
            student_status = frappe.get_value("Student", self.student, "student_status")
            subject = "Attendance Entry for Early Pickup - " + self.student
            notice_text = f"Early Attendance Entry has been created/updated for student {self.student_name}({self.student}) of class {class_attr} on {timestamp}"

            notice = frappe.get_doc(
                {
                    "doctype": "School Notice",
                    "class": class_attr,
                    "is_generic_notice": 0,
                    "school": school,
                    "subject": subject,
                    "student": self.student,
                    "division": division,
                    "student_status": student_status,
                    "notice": notice_text,
                    "academic_year": academic_year,
                    "is_raw_html": 1,
                }
            ).insert(ignore_permissions=True)

            users = [
                user.user
                for user in frappe.get_all(
                    "User Permission",
                    {"allow": "School", "for_value": school},
                    ["user"],
                )
                if check_councellor_role(user.user)
            ]
            for user in users:
                notification_sender(user, self.student, subject, notice_id=notice.name)
        except:
            frappe.log_error(
                "Error Sending Notification to Councellor", frappe.get_traceback()
            )


def check_councellor_role(user):
    roles = frappe.get_roles(user)
    return "Councellor" in roles
