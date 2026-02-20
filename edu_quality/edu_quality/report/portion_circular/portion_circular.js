// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Portion Circular"] = {
	"filters": [
		{
			"fieldname": "division",
			"fieldtype": "Link",
			"options": "Student Group",
			"label": "Division"
		}, {
			"fieldname": "unit",
			"label": __("Unit"),
			"fieldtype": "Select",
			"options": [1, 2, 3, 4],
			"reqd": 1,
		},
		, {
			"fieldname": "subject",
			"label": __("Subject"),
			"fieldtype": "Link",
			"options": "Course",

		},
	]
};
