// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Petty Cash"] = {
	filters: [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
		},
		{
			"fieldname": "school",
			"label": __("School"),
			"fieldtype": "Link",
			"options": "School",
		},
		{
			"fieldname": "type",
			"label": __("Type"),
			"fieldtype": "Select",
			"options": ["Payment", "Cash Withdrawal"],
		},
		{
			"fieldname": "date",
			"label": __("Select Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		}
	],
};
