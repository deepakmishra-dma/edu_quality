# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PaymentPlan(Document):
	def autoname(self):
		self.name = get_formatted_payment_plan(self)

	def before_validate(self):
		terms = []
		for schedule in self.payment_schedule:
			if schedule.payment_term:
				if schedule.payment_term in terms:
					frappe.throw("Payment Term cannot be repeated")
				else:
					terms.append(schedule.payment_term)

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

		# due date cannot be less than previous due date
		for i in range(1, len(self.payment_schedule)):
			if self.payment_schedule[i].due_date < self.payment_schedule[i-1].due_date:
				frappe.throw("Due Date cannot be less than previous Due Date")

	def validate_existing_payment_plan(self):
		existing_payment_plan = frappe.db.get_all("Payment Plan", {
			"academic_year": self.academic_year,
			"school": self.school,
			"program": self.program,
		}, ["name"])
		if existing_payment_plan:
			for plan in existing_payment_plan:
				if self.get_doc_before_save() and plan.name == self.name:
					continue
				else:
					existing_payment_plan_doc = frappe.get_doc("Payment Plan", plan.name)
					existing_schedule = existing_payment_plan_doc.payment_schedule
					if len(existing_schedule) == len(self.payment_schedule):
						# Compare payment terms, due dates, and invoice portions
						is_identical = all(
							term.payment_term == existing_term.payment_term and
							term.invoice_portion == existing_term.invoice_portion
							for term, existing_term in zip(self.payment_schedule, existing_schedule)
						)
						if is_identical:
							frappe.throw("Identical Payment Plan already exists")



def get_formatted_payment_plan(data):
    program = data.program
    academic_year = data.academic_year

    invoice_portions = []
    for ps in data.payment_schedule:
        invoice_portions.append(str(ps.invoice_portion))
    formatted_invoice_portions = "-".join(invoice_portions)
    data.plan_name = f"{data.plan_name}-({formatted_invoice_portions})"
    formatted_payment_plan = f"{data.plan_name}-{program}-({academic_year})"
    return formatted_payment_plan