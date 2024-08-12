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
		{
			"fieldname": "academic_year",
			"label": __("Academic Year"),
			"fieldtype": "Link",
			"options": "Academic Year",
			"width": "80",
		},
	],

	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true
		});
	},

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
			let indexes = frappe.query_report.datatable.rowmanager.getCheckedRows();
			let selected_rows = indexes.map(i => frappe.query_report.data[i]);

			if (selected_rows.length == 0) {
				frappe.msgprint(__("Select a Student before Marking as Defaulter"))
				return
			}
			console.log(selected_rows);
			frappe.confirm('Are you sure you want to proceed?',
				() => {
					frappe.call({
						method: "edu_quality.fees.report.fees_defaulter_report.fees_defaulter_report.mark_as_defaulter",
						type: "POST",
						args: {
							data: selected_rows
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
