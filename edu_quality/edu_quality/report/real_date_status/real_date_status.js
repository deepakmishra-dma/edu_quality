// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Real Date Status"] = {
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
		{
			"fieldname": "class",
			"fieldtype": "Link",
			"options": "Class Type",
			"label": "Class",
		},
		{
			"fieldname": "subject",
			"fieldtype": "Link",
			"options": "Course",
			"label": "Subject",
		},
		{ "fieldname": "show_blank", "default": 1, "fieldtype": "Check", "label": "Show Blank" },
	]
};
