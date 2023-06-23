# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ReferenceNumberSettings(Document):
	pass

@frappe.whitelist()
def generate_next(doc):
	doc = frappe.get_doc("Reference Number Settings",doc)
	doc1 = frappe.get_doc({
		"doctype": "Reference Number Settings",
		"academic_year":frappe.get_last_doc("Academic Year").name
	})
	for school in doc.prefixes:
		doc1.append("prefixes",{
			"school":school.school,
			"prefix":school.prefix
		})
	program = ''
	prefix = '--'
	for prog in doc.reference_numbers:
		program = prog.program
		doc1.append("reference_numbers",{
			"program":program,
			"series":prefix
		})
		prefix = prog.series 
	doc1.insert()

		
