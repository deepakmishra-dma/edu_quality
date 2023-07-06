# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentPlan(Document):
	def before_validate(self):
		invoice_portion = 0
		for schedule in self.payment_schedule:
			if schedule.invoice_portion:
				invoice_portion += float(schedule.invoice_portion)
		if invoice_portion != 100:
			frappe.throw("Invoice Portion should be equal to 100")
		else:
			for schedule in self.payment_schedule:
				if schedule.invoice_portion:
					schedule.payment_amount = self.total_amount * (schedule.invoice_portion/100)
				elif schedule.payment_amount:
					schedule.invoice_portion = (schedule.payment_amount/self.total_amount) *100


