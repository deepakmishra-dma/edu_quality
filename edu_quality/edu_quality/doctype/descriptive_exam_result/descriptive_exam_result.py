# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import education.education
import frappe
from education.education.doctype.assessment_result.assessment_result import (
	AssessmentResult,
)
from frappe.model.document import Document


class DescriptiveExamResult(Document):
	def validate(self):
		# education.education.validate_student_belongs_to_group(
		#     self.student, self.student_group
		# )
		pass

	def process_result(self):
		for question in self.questions:
			program_name = frappe.db.get_value("Program", self.program, "program_name")
			verbose_meaning = frappe.db.get_value(
				"Descriptive Marks Setup",
				{"class_type": program_name, "marks": question.score},
				"verbose_meaning",
			)
			question.verbose_meaning = verbose_meaning

	def validate_processed_result(self):
		if self.docstatus in [1, 2]:
			return

		self.process_result()

	def before_submit(self, method=None):
		self.process_result()
