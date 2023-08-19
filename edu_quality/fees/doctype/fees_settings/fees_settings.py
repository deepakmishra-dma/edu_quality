# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FeesSettings(Document):
	def validate(self):
		#validate duplicates in Application Fees
		i=0
		j=0
		for ap_fee in self.application_fees:
			j=0
			for next in self.application_fees:
				if i!=j and ap_fee.class_name == next.class_name and ap_fee.academic_year == next.academic_year:
					frappe.throw("Application fee for " + next.class_name + "-" + next.academic_year + " Already Exists!")
				j+=1
			i+=1




