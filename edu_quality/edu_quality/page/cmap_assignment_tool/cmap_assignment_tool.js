let globalTableRef = null
frappe.pages['cmap-assignment-tool'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'CMAP Assignment Tool',
		single_column: true
	});
	const el = document.querySelector('.container.page-body')
	const d = make_fieldgroup(el, [
		{
			label: 'Academic Year',
			fieldname: 'academic_year',
			fieldtype: 'Link',
			options: "Academic Year"
		},
		{
			label: 'Class',
			fieldname: 'class',
			fieldtype: 'Link',
			options: "Program"
		}, {
			label: 'Subject',
			fieldname: 'subject',
			fieldtype: 'Link',
			options: "Course"
		}, {
			label: 'Unit',
			fieldname: 'unit',
			fieldtype: 'Select',
			options: ["1", "2", "3", "4"]
		},


	])
	
	const tableContainer = document.createElement('div')
	tableContainer.id = 'report-table-container'

	wrapper.appendChild(tableContainer)
	setupDataTable()
}
function setupDataTable() {
	const container = document.getElementById('report-table-container')
	return new DataTable(container, {
		columns: ['Period No', 'Chapter Name', 'Division', 'Teacher', 'Plan Date'],
		data: [
			['Tiger Nixon', 'System Architect', 'Tech'],
			['Garrett Winters', 'Accountant', '']
		]
	});
}

function make_fieldgroup(parent, ddf_list) {
	fg = new frappe.ui.FieldGroup({
		"fields": ddf_list,
		"parent": parent
	});
	fg.make();
	console.log(fg)
	return fg

}