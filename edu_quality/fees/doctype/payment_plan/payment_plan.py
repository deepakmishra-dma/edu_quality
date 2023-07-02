# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class PaymentPlan(Document):
	def before_save(self):
		for schedule in self.payment_schedule:
			if schedule.invoice_portion:
				schedule.payment_amount = self.total_amount * (schedule.invoice_portion/100)
			elif schedule.payment_amount:
				schedule.invoice_portion = (schedule.payment_amount/self.total_amount) *100


