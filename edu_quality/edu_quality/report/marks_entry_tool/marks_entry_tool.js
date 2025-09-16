// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
function changeMarksData(value, columnId, rowIndex, maximum_score) {
	console.log(frappe.query_report.data[rowIndex])
	if (Number(value.value) > Number(maximum_score)) {
		const inputEl = document.querySelector(`input[column='${columnId}'][rowindex='${rowIndex}']`)


		inputEl.value = undefined
		frappe.query_report.data[rowIndex][columnId] = undefined
		return
	}
	frappe.query_report.data[rowIndex][columnId] = value.value


}
frappe.query_reports["Marks Entry Tool"] = {
	"filters": [
		{
			"fieldname": "academic_year",
			"fieldtype": "Link",
			"options": "Academic Year",
			"label": "Academic Year",
			get_query: "edu_quality.public.py.utils.academic_year_query"


		},
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
			"options": "Class Type",
			"reqd": 1,

			// get_data: function (txt) {
			// 	return frappe.db.get_link_options('Class Type', txt, {

			// 	});
			// }

		},
		{
			"fieldname": "assessment_group",
			"label": __("Assessment Group"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Assessment Group",
			get_query: {
				filters: { "custom_is_composite": 0 }
			}
		},
		{
			"fieldname": "division",
			"label": __("Division"),
			"fieldtype": "Link",
			"options": "Student Group",
			"reqd": 1,

			// const res = await frappe.call({
			// 		"method": "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.get_divisions_class_type", args: {
			// 			"txt": txt,
			// 			"filters": {
			// 				"school": frappe.query_report.get_filter_value("school"),
			// 				"class": frappe.query_report.get_filter_value("program"),
			// 				"academic_year": frappe.query_report.get_filter_value("academic_year")
			// 			}
			// 		}
			// 	})
			// return res?.message
			// }


		},
	],

	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data)
		if (column.is_criteria) {
			value = `<input type="text" column="${column.fieldname}" rowindex=${row[0]?.rowIndex} max="${column.maximum_score}" maximum-score="${column.maximum_score}" value="${value}" oninput="changeMarksData(this,'${column.id}','${row[0]?.rowIndex}','${column.maximum_score}')" />`
		}

		return value
		// console.log(value)
	}, "onload": function (report) {

		report.page.add_inner_button(__('Save Marks Entry'), () => {
			let message = `
			<div>	
				<p>Are you sure you want to Save Marks Entered?</p>
			</div>`;



			frappe.confirm(__(message), () => {
				const filters = {}; frappe.query_report.filters.forEach((filter) => {
					filters[filter.fieldname] = frappe.query_report.get_filter_value(filter.fieldname)
				}
				)
				frappe.call({
					"method": "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.do_mark_entry",
					args: {
						data: frappe.query_report.data,
						filters: filters,
					}
				})
			})
		})

	},

};
