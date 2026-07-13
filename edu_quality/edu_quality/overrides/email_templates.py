import urllib.parse

import frappe
from frappe.email.doctype.email_template.email_template import EmailTemplate


class CustomEmailTemplate(EmailTemplate):
	def on_trash(self):
		self.validate_funnel(is_delete=True)

	def on_update(self):
		self.validate_funnel()

	def validate_funnel(self, is_delete=False):
		funnels = frappe.get_all(
			"Funnel Definition",
			{
				"element_type": "Action",
				"data": ["like", f'%"email_template": "{self.name}"%'],
				"parenttype": "Funnel",
			},
			pluck="parent",
		)

		if funnels:
			funnels_encoded = [urllib.parse.quote_plus(name) for name in funnels]
			funnels_string = ",".join(f'"{name}"' for name in funnels_encoded)
			link = f'/app/funnel?name=["in",[{funnels_string}]]'
			msg = f'The Email Template "{self.name}" is being used in the following Funnels:<ul style="padding-left: 15px;">{" ".join(f"<li>{funnel}</li>" for funnel in funnels)}</ul>\n<div style="text-align: right;"><a href="{link}" target="_blank" class="btn btn-primary">Open Funnel List</a></div>'

			if is_delete:
				frappe.throw(
					title=frappe._("Email Template in Use"),
					msg=frappe._(msg),
				)
			else:
				frappe.msgprint(
					title=frappe._("Email Template in Use"),
					msg=frappe._(msg),
				)
