# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SecurityDeposit(Document):
    def after_insert(self):
        doc = frappe.get_doc({
        
            "doctype": "Fee Category",
            "category_name": self.name,
            'type':"Deposit"
            'custom_company': "Unique Educational and Sports Foundation"
        })
        doc.insert()
