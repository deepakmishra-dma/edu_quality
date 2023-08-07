# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime
from frappe.model.document import Document

class FeeReceipt(Document):
	def before_save(self):
		if self.due_date and self.paid_on:
			due_date = self.due_date
			paid_on = self.paid_on
			if type(self.due_date) != str:
				due_date = self.due_date.strftime("%Y-%m-%d")
			if type(self.paid_on) != str:
				paid_on = self.paid_on.strftime("%Y-%m-%d")
			
			difference = (datetime.strptime(due_date, "%Y-%m-%d") - datetime.strptime(paid_on, "%Y-%m-%d")).days 
			color = "Green"
			if difference == 0:
				color = "Yellow"
			elif difference < 0 and difference>=-5:
				color = "Orange"
			elif difference < -5:
				color = "Red"
			self.payment_grade = color


