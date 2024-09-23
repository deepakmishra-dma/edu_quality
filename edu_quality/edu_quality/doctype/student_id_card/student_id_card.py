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
