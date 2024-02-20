# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CMAP(Document):
    def autoname(self, method=None):
        textbook_shortcode = frappe.db.get_value("Textbook", self.texbook, "short_code")
        course_doc = frappe.get_doc("Course", self.subject)
        class_sortcode = frappe.db.get_value(
            "Class Type", self.get("class"), "short_code"
        )
        self.name = f"{self.academic_year}-{course_doc.name}{textbook_shortcode}{class_sortcode}{self.unit}{self.period} - {self.chapter}"
