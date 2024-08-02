// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Fees Defaulter Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
		},
		{
			"fieldname": "school",
			"label": __("School"),
			"fieldtype": "MultiSelectList",
			"options": "School",
			"width": "80",
			get_data: function (txt) {
				return frappe.db.get_link_options('School', txt);
			}
		},
		{
			"fieldname": "program",
			"label": __("Class"),
			"fieldtype": "MultiSelectList",
			"options": "Class",
			"width": "80",
			get_data: function (txt) {
				return frappe.db.get_link_options('Program', txt);
			}
		},
		{
			"fieldname": "term",
			"label": __("Term"),
			"fieldtype": "Link",
			"options": "Payment Term",
			"width": "80",
		},
		{
			"fieldname": "student_status",
			"label": __("Student Status"),
			"fieldtype": "Select",
			"options": ["", "New student", "Current student", "Cancelled", "Not attending", "Defaulter", "Alumni"],
			"width": "80",
		},
	],

	onload: function (report) {
		report.page.add_inner_button(__('Payment Reminder'), function () {
			frappe.confirm('Are you sure you want to proceed?',
				() => {
					var filters = report.get_values();
					if (filters.school) {
						frappe.call({
							method: "edu_quality.fees.report.fees_defaulter_report.fees_defaulter_report.send_payment_reminder",
							type: "POST",
							args: {
								from_date: filters.from_date,
								to_date: filters.to_date,
								school: filters.school,
								program: filters.program,
								term: filters.term,
								student_status: filters.student_status
							},
							callback: function (r) {
								if (r.message) {
									if (r.message.title == "Success") {
										frappe.show_alert({
											message: __(r.message.msg),
											indicator: 'green'
										});
									} else if (r.message.title == "Error") {
										frappe.show_alert({
											message: __(r.message.msg),
											indicator: 'red'
										});
									}
								}
							}
						});
					}
					else {
						frappe.show_alert({
							message: __("Please select School"),
							indicator: 'red'
						});
					}
				}, () => {
					frappe.show_alert({
						message: __("Action Cancelled"),
						indicator: 'red'
					});
				});
		});

		report.page.add_inner_button(__('Mark As Defaulter'), function () {
			frappe.confirm('Are you sure you want to proceed?',
				() => {
					var filters = report.get_values();
					if (filters.school) {
						frappe.call({
							method: "edu_quality.fees.report.fees_defaulter_report.fees_defaulter_report.change_student_status",
							type: "POST",
							args: {
								from_date: filters.from_date,
								to_date: filters.to_date,
								school: filters.school,
								program: filters.program,
								term: filters.term,
								student_status: filters.student_status,
							},
							callback: function (r) {
								if (r.message) {
									if (r.message.title == "Success") {
										frappe.show_alert({
											message: __(r.message.msg),
											indicator: 'green'
										});
									} else if (r.message.title == "Error") {
										frappe.show_alert({
											message: __(r.message.msg),
											indicator: 'red'
										});
									}
								}
							}
						});
					}
					else {
						frappe.show_alert({
							message: __("Please select School"),
							indicator: 'red'
						});
					}
				}, () => {
					frappe.show_alert({
						message: __("Action Cancelled"),
						indicator: 'red'
					});
				});
		}
		);
	}
};
