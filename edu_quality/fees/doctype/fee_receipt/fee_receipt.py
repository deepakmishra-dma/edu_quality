# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from frappe.model.document import Document

class FeeReceipt(Document):
	def before_save(self):
		if self.due_date and self.paid_on:
			difference = (datetime.strptime(self.due_date, "%Y-%m-%d")- datetime.strptime(self.paid_on, "%Y-%m-%d")).days 
			color = "Green"
			if difference == 0:
				color = "Yellow"
			elif difference < 0 and difference>=-5:
				color = "Orange"
			elif difference < -5:
				color = "Red"
			self.payment_grade = color


