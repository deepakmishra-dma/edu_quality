// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Unassigned Instructors"] = {
	"filters": [
		{
			"fieldname": "academic_year",
			"fieldtype": "Select",
			"options": ["2023-2024", "2024-2025"],
			"label": "Academic Year",
		},
		{
			"fieldname": "school",
			"fieldtype": "Link",
			"options": "School",
			"label": "School",
		},
	]
};
