import frappe
from education.education.doctype.student.student import Student
from frappe.auth import LoginManager
from edu_quality.edu_quality.server_scripts.guardian import set_guardian_permissions

class CustomStudent(Student):
    def validate_user(self):
        current_user = frappe.session.user 
        login_manager = LoginManager()
        login_manager.login_as("Administrator")
        """Create a website user for student creation if not already exists"""
        if not frappe.db.get_single_value(
            "Education Settings", "user_creation_skip"
        ) and not frappe.db.exists("User", self.student_email_id):
            student_user = frappe.get_doc(
                {
                    "doctype": "User",
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "email": self.student_email_id,
                    "gender": self.gender,
                    "send_welcome_email": 0,
                    "user_type": "Website User",
                }
            )
            student_user.add_roles("Student")
            student_user.save(ignore_permissions=True)

            self.user = student_user.name
        login_manager.login_as(current_user)


    def on_update(self):
        # Giving permissions to guardian
        set_guardian_permissions(self)
