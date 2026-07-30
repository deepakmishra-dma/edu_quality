# Copyright (c) 2026, Walnut and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class AdmissionTarget(Document):
	def validate(self):
		self.set_school()
		self.check_duplicate()

	def set_school(self):
		if self.program:
			self.school = frappe.db.get_value("Program", self.program, "school")

	def check_duplicate(self):
		existing = frappe.db.exists(
			"Admission Target",
			{
				"academic_year": self.academic_year,
				"program": self.program,
				"name": ("!=", self.name),
			},
		)
		if existing:
			frappe.throw(
				_("A target for {0} in {1} already exists: {2}").format(
					frappe.bold(self.program), frappe.bold(self.academic_year), existing
				),
				frappe.DuplicateEntryError,
			)
