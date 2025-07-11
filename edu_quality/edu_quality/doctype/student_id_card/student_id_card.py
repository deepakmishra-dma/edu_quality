# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class StudentIDCard(Document):
    def autoname(self):
        student = frappe.get_value(
            "Program Enrollment", self.program_enrolled_in, "student"
        )
        academic_year = frappe.get_value(
            "Program Enrollment", self.program_enrolled_in, "academic_year"
        )
        name = make_autoname(student + "-{" + academic_year + "}-.###")
        self.name = name.replace("{", "(").replace("}", ")")

    def on_update(self):
        old_doc = self.get_doc_before_save()
        if old_doc and old_doc.status != self.status:
            frappe.get_doc(
                {
                    "doctype": "ID Card Event",
                    "timestamp": frappe.utils.now(),
                    "parenttype": "Student ID Card",
                    "parentfield": "events",
                    "status": "RECEIVED BY STUDENT",
                    "user": frappe.session.user,
                    "parent": self.name,
                }
            ).insert(ignore_permissions=True)

        program_enrollment = frappe.get_doc(
            "Program Enrollment", self.program_enrolled_in
        )
        if not old_doc or (old_doc and old_doc.photo_taken != program_enrollment.image):
            program_enrollment.image = self.photo_taken
            program_enrollment.save(ignore_permissions=True)
