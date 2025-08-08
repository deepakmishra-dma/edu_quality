// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Marks Entry Tool"] = {
	"filters": [
		{
			"fieldname": "school",
			"fieldtype": "Link",
			"options": "School",
			"label": "School",

		},
		{
			"fieldname": "program",
			"label": __("Class"),
			"fieldtype": "Link",
			"options": "Program",
			"reqd": 1,
			get_data: function (txt) {
				console.log(frappe.query_report.get_filter_value("school"), "haha"
				)
				return frappe.db.get_link_options('Program', txt, {

					"school": frappe.query_report.get_filter_value("school") || ""

				});
			}
			// get_data: function (txt) {
			// 	return frappe.db.get_link_options('Class Type', txt, {

			// 	});
			// }

		},
		{
			"fieldname": "division",
			"label": __("Division"),
			"fieldtype": "MultiSelectList",
			"reqd": 1,
			get_data: function (txt) {

				return frappe.db.get_link_options('Student Group', txt, {

					"program": frappe.query_report.get_filter_value("program") || ""

				});
			}

		},
		{
			"fieldname": "assessment_group",
			"label": __("Assessment Group"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Assessment Group"

		},

	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data)
		if (column.is_criteria) {
			value = `<input type="number" id="${column.fieldname}" value=${value} oninput="changePrintCMAPReportData(this,'${column.id}','${row[0]?.rowIndex}')" />`
		}

		return value
		// console.log(value)
	}, "onload": function (report) {

		report.page.add_inner_button(__('Save Marks Entry'), () => {
			let indexes = frappe.query_report.datatable.rowmanager.getCheckedRows();
			let selected_rows = indexes.map(i => frappe.query_report.data[i]);

			if (selected_rows.length == 0) {
				frappe.msgprint(__("Select a row before creating Purchase Order"))
				return
			}
			let message = `
				<div>
					
					<p>Are you sure you want to create a Purchase Order, for the selected rows ?</p>
				</div>`;



			frappe.confirm(__(message), () => {
				const academic_year = report.filters.find(el => el.fieldname === "academic_year").input.value
				const class_name = report.filters.find(el => el.fieldname === "class").input.value

				frappe.call({
					"method": "edu_quality.edu_quality.report.cmap_print.cmap_print.create_purchase_order",
					"args": {
						rows: selected_rows,
						academic_year: academic_year,
						class_name: class_name
					},
					callback: function (r) {
						if (r.message) {
							frappe.set_route(`/app/purchase-order/${r?.message?.name}`)
						}
					}
				})
			})
		})

	},

};
