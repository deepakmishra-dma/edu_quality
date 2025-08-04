# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def date_to_words(date):
	return 1


class StudentExit(Document):
	def before_insert(self):
		self.requested_on = frappe.utils.nowdate()
		self.update_details()

	def update_details(self):
		student = frappe.get_doc("Student",self.student)
		try:
			fee,deposit,account = student.check_deposit(deduct=1)
			self.deposit_amount = deposit
			self.pending_fees = student.check_pending_fee()
			if self.pending_fees:
				self.fees_status = "Unpaid"
			else:
				self.fees_status = "Paid"
			for guardian in student.guardians:
				if guardian.relation == 'Father':
					self.father_name = guardian.guardian_name
				elif guardian.relation == 'Mother':
					self.mother_name = guardian.guardian_name
				else:
					guardian_name = guardian.guardian_name
			if not self.father_name:
				self.father_name = guardian_name		
			self.dob_in_words = date_to_words(student.date_of_birth)	
			self.get_fee_details()
		except Exception as e:
			self.deposit_amount = 0 
			self.refund_amount = 0
	

	def get_fee_details(self):
		last_paid_fee = frappe.db.get_all("Fees",filters=[["Fees","student","=","SHFA21"],["Payment Schedule","outstanding","=",0]],order_by="creation desc",limit=1)
		if last_paid_fee:
			self.fees_paid_upto = frappe.db.get_all("Payment Schedule",{'parent':last_paid_fee[0].name,'outstanding':0},'due_date',order_by="payment_term desc",limit=1)[0]
			fee = frappe.get_doc("Fees",last_paid_fee[0].name)
			for component in fee.components:
				if component.custom_discounts:
					self.discount_details = self.discount_details + ", "+component.custom_discounts
			self.discount_details = self.discount_details + "Total Amount - " + str(fee.total_discount)


	def on_submit(self):
		student = frappe.get_doc("Student", self.student)
		student.custom_cancellation_letter = self.cancellation_letter
		student.date_of_leaving = self.date_of_leaving 
		student.leaving_certificate_number = self.leaving_certificate_number
		student.save(ignore_permissions=True)
		student.cancel_student(self.academic_year,self.cancellation_type)
