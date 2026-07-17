import frappe

data = [
	{"doctype": "Fees", "link_doctype": "Payment Request", "link_field": "reference_name", "group": None},
	{"doctype": "Fees", "link_doctype": "Payment Entry", "link_field": "fees", "group": None},
	{"doctype": "Student", "link_doctype": "Payment Request", "link_field": "party", "group": None},
	{"doctype": "Student", "link_doctype": "Payment Entry", "link_field": "party", "group": None},
]


def update_links():
	for l in data:
		try:
			d = frappe.get_doc("Customize Form")
			if l["doctype"]:
				d.doc_type = l["doctype"]
			d.run_method("fetch_to_customize")
			for link in d.get("links"):
				if link.link_doctype == l["link_doctype"] and link.link_fieldname == l["link_field"]:
					# found so just return
					return
			d.append(
				"links",
				dict(
					link_doctype=l["link_doctype"],
					link_fieldname=l["link_field"],
					table_fieldname=None,
					group=l["group"],
				),
			)
			d.run_method("save_customization")
			frappe.clear_cache()
		except Exception as e:
			frappe.log_error(title="Migrate Error", message=frappe.get_traceback())
