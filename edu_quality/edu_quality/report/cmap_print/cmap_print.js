// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
function changePrintCMAPReportData(value, id, rowIndex) {

	frappe.query_report.data[rowIndex][id] = value.value
	calculateTotalQty(rowIndex)
}

function calculateTotalQty(rowIndex) {
	const totalQty = frappe.query_report.data[rowIndex]["qty_for_shivane"] + frappe.query_report.data[rowIndex]["qty_for_wakad"] + frappe.query_report.data[rowIndex]["qty_for_fursungi"] + frappe.query_report.data[rowIndex]["extra_qty_per_school"]
	frappe.query_report.data[rowIndex]["total_quantity"] = totalQty
}
frappe.query_reports["CMAP Print"] = {
	"filters": [
		{
			"fieldname": "academic_year",
			"fieldtype": "Link",
			"options": "Academic Year",
			"label": "Academic Year"
		},
		{
			"fieldname": "class",
			"label": __("Class"),
			"fieldtype": "MultiSelectList",
			"reqd": 1,
			get_data: function (txt) {
				return frappe.db.get_link_options('Class Type', txt, {

				});
			}

		},
		{
			"fieldname": "subject",
			"label": __("Subject"),
			"fieldtype": "MultiSelectList",
			"reqd": 1,
			get_data: function (txt) {
				return frappe.db.get_link_options('Course', txt, {

				});
			}

		},
		{
			"fieldname": "unit",
			"label": __("Unit"),
			"fieldtype": "MultiSelectList",
			"reqd": 1,
			get_data: function (txt) {
				return [{ value: 1, description: 1 }, { value: 2, description: 2 }, { value: 3, description: 3 }, { value: 4, description: 4 }]
			}

		},
		{
			"fieldname": "start_plan_date",
			"fieldtype": "Date",
			"label": "Start Plan Date"
		}, {
			"fieldname": "end_plan_date",
			"fieldtype": "Date",
			"label": "End Plan Date"
		},
	],
	"formatter": function (value, row, column, data, default_formatter) {

		console.log(row, column)
		value = default_formatter(value, row, column, data)
		if (column.id.includes("qty")) {
			value = `<input type="number" value=${value} oninput="changePrintCMAPReportData(this,'${column.id}','${row[0]?.rowIndex}')" />`
			console.log(frappe.query_report)
		}
		return value
		// console.log(value)
	}
};
