# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DescriptiveQuestionPaper(Document):
    def before_insert(self, method=None):
        descriptive_exam_doc = frappe.get_doc("Descriptive Exam", self.descriptive_exam)
        for question in descriptive_exam_doc.questions:
            if question.get("selected"):
                self.append("questions", {"question": question.get("question")})
