# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt
import json
import frappe
from edu_quality.public.py.application import enroll_student
from frappe.model.document import Document
class MGREnrollmentLog(Document):
    def before_insert(self):
        try:
            student_applicant = frappe.get_value("Student Applicant", {"lms_id": self.lms_id})
            if student_applicant:
                application_status = frappe.get_value(
                    "Student Applicant", student_applicant, "application_status"
                )
                if application_status == "Admitted":
                    self.enrollment__status = "Failed"
                    self.responce = "Student already enrolled"
                    return
                frappe.set_user("Administrator")
                data = json.loads(self.responce) if self.responce else {}
                enroll_student(student_applicant, self.email, self.ref_no, data)
                self.enrollment__status = "Success"
                self.responce = "Success"
            else:
                self.enrollment__status = "Failed"
                self.responce = "Student Applicant not found"
        except Exception as e:
            self.enrollment__status = "Failed"
            self.responce = frappe.get_traceback()
            frappe.logger("enrollment").exception(e)
    
