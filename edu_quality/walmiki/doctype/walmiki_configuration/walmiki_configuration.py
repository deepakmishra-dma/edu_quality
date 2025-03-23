# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class WalmikiConfiguration(Document):
	def before_save(self):
		self.update_scripts()

	def update_scripts(self):
		for document in self.triggers:
			script_name = "walmiki_"+ document.document_type.lower() + "_" + document.trigger.lower()	
			if frappe.db.exists("Server Script", script_name):
				script = frappe.get_doc("Server Script", script_name)
			else:
				script = frappe.new_doc("Server Script")
				script.name = script_name
			script.script_type = "DocType Event"
			script.reference_doctype = document.document_type
			script.doctype_event = document.trigger
			config = frappe.get_doc("Walmiki Configuration")
			url = config.base_url + document.endpoint
			script.script = """frappe.call("{0}",doctype="{1}",docname=doc.name,url="{2}")""".format(document.method,document.document_type,url)
			script.save(ignore_permissions=True)
			
