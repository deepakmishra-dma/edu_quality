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
                frappe.db.set_value("Student Applicant",student_applicant,"student_email_id",self.email)
                if application_status == "Admitted":
                    self.enrollment__status = "Failed"
                    self.erp_responce = "Student already enrolled"
                    return
                frappe.set_user("Administrator")
                data = json.loads(self.responce) if self.responce else {}
                enroll_student(student_applicant, self.email, self.ref_no, data,data.get("division"))
                self.enrollment__status = "Success"
                self.erp_responce = "Success"
            else:
                self.enrollment__status = "Failed"
                self.erp_responce = "Student Applicant not found"
        except Exception as e:
            self.enrollment__status = "Failed"
            self.erp_responce = frappe.get_traceback()
            frappe.logger("enrollment").exception(e)

@frappe.whitelist()    
def re_enroll_student(id):
    try:
        doc = frappe.get_doc("MGR Enrollment Log",id)
        data = json.loads(doc.responce) if doc.responce else {}
        student_applicant = frappe.get_value("Student Applicant", {"lms_id": doc.lms_id})
        enroll_student(student_applicant, doc.email, doc.ref_no, data,data.get("division"))
        doc.enrollment__status = "Success"
        doc.erp_responce = "Success"
        doc.save(ignore_permissions=True)
    except Exception as e:
        doc.enrollment__status = "Failed"
        doc.erp_responce = frappe.get_traceback()
        doc.save(ignore_permissions=True)
        frappe.logger("enrollment").exception(e)
