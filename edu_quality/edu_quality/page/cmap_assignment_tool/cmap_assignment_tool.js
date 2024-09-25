let globalTableRef = null
let filtersRef = null

frappe.pages['cmap-assignment-tool'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'CMAP Assignment Tool',
		single_column: true
	});
	const el = document.querySelector('.container.page-body')
	filtersRef = make_fieldgroup(el, [
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
			options: "Class Type"
		}, {
			label: 'Subject',
			fieldname: 'subject',
			fieldtype: 'Link',
			options: "Course"
		}, {
			label: 'School',
			fieldname: 'school',
			fieldtype: 'Link',
			options: "School"
		}, {
			label: 'Unit',
			fieldname: 'unit',
			fieldtype: 'Select',
			options: ["1", "2", "3", "4"]
		},
		{
			label: 'Button', fieldtype: "Button", click: () => {
				getDivisions()
				getCmap()
			}
		}

	])

	const tableContainer = document.createElement('div')
	const editContainer = document.createElement('div')
	editContainer.id = 'report-edit-container'
	tableContainer.id = 'report-table-container'

	wrapper.appendChild(tableContainer)
	wrapper.appendChild(editContainer)
	setupDataTable()
	editMode()
}
function editMode() {
	const container = document.getElementById('report-edit-container')
	make_fieldgroup(container, [
		{
			label: 'Division',
			fieldname: 'division',
			fieldtype: 'Link',
			options: "Student Group"
		},
		{
			label: 'Teacher',
			fieldname: 'teacher',
			fieldtype: 'Link',
			options: "Instructor"
		},
		{ label: 'Button', fieldtype: "Button", click: getDivisions }

	])
}
function getFilters() {
	const filters = {}
	console.log(filtersRef.fields_dict, 'sadada')
	if (filtersRef && filtersRef.fields_dict)
		Object.keys(filtersRef.fields_dict).forEach(key => {
			console.log(key, filtersRef.fields_dict[key])
			filters[key] = filtersRef.fields_dict[key].value
		})
	console.log(filters, 'yyoo')
	return filters
}

async function getDivisions() {
	const filters = getFilters()
	const divisionsData = await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.get_divisions',
		args: filters
	})
	console.log(divisionsData, 'ho')
}
async function getCmap() {
	const filters = getFilters()
	const cmapData = await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.get_cmap',
		args: filters
	})
	setupDataTable(cmapData?.message || {})
}

function setupDataTable(cmapData) {
	const container = document.getElementById('report-table-container')
	console.log(container)
	container.innerHTML = ""
	container.appendChild(createTable(cmapData))

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

function createTable(data) {
	const table = document.createElement('table');

	const thead = document.createElement('thead')
	const tbody = document.createElement('tbody')
	const headerRow = document.createElement('tr');

	const headerCell1 = document.createElement('th');
	headerCell1.textContent = 'Peroid No.';
	headerRow.appendChild(headerCell1);

	const headerCell2 = document.createElement('th');
	headerCell2.textContent = 'Chapter Name';
	headerCell2.colSpan = 2;
	headerRow.appendChild(headerCell2);

	const headerCell3 = document.createElement('th');
	headerCell3.textContent = 'Division';
	headerRow.appendChild(headerCell3);

	const headerCell4 = document.createElement('th');
	headerCell4.textContent = 'Teacher';
	headerRow.appendChild(headerCell4);

	const headerCell5 = document.createElement('th');
	headerCell5.textContent = 'Plan Date';
	headerRow.appendChild(headerCell5);

	const headerCell6 = document.createElement('th');
	headerCell6.textContent = 'Note';
	headerRow.appendChild(headerCell6);
	console.log(data, 'asade')
	if (data)
		Object.keys(data).forEach(val => {
			data[val].forEach((row, index) => {
				const row_html = createRow(val, '231', row.division_name, row.teacher, row.plan_date, 'adad', index === 0, data[val].length)
				tbody.innerHTML += (row_html)
			})
		})
	console.log(headerRow)
	thead.appendChild(headerRow)
	table.appendChild(thead);

	table.appendChild(tbody);
	return table
}

function createRow(period_no, chapter_name, division, teacher, plan_date, note, first_row, rowSpan) {
	console.log(rowSpan)
	if (first_row)
		return `<tr>
	<td rowspan="${rowSpan}">${period_no}</td>
	<td rowspan="${rowSpan}">${chapter_name}</td>
	<td>${division}</td>
	<td class="teacher-cell"><select value="${teacher}"><option>test</option></select></td>
	<td>${plan_date}</td>
	<td>${note}</td>
  </tr>
  `
	return `<tr>

  <td>${division}</td>
  <td class="teacher-cell"><select value="${teacher}"><option>test</option></select></td>
  <td>${plan_date}</td>
  <td>${note}</td>
</tr>

`
}

function createSelect(selectData) {

}