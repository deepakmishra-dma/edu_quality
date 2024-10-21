let globalTableRef = null
let filtersRef = null
let cmapData = []
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
	const d = make_fieldgroup(container, [
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
		{ label: 'Apply', fieldtype: "Button", click: () => changeCmapDataBulk(d) },
		{ label: 'Save', fieldtype: "Button", click: () => saveAssignment() }

	])
}

function changeCmapDataBulk(fieldGroup) {
	const division = fieldGroup.fields_dict["division"].value
	const teacher = fieldGroup.fields_dict["teacher"].value
	console.log(division)
	Object.keys(cmapData).forEach(key => cmapData[key].forEach((values, index) => {

		if (values.division_name == division) {
			cmapData[key][index] = { ...cmapData[key][index], teacher }
			
		}

	}))
	console.log(cmapData)
	setupDataTable()
}

function changeTeacherOnSelect(e) {
	const dataset = e.target.dataset

	if (dataset.index && dataset.key && cmapData) {
		cmapData[dataset.key][dataset.index].teacher = e.target.value

		// setupDataTable(cmapData)
	}

}
function getFilters() {
	const filters = {}

	if (filtersRef && filtersRef.fields_dict)
		Object.keys(filtersRef.fields_dict).forEach(key => {

			filters[key] = filtersRef.fields_dict[key].value
		})

	return filters
}

async function getDivisions() {
	const filters = getFilters()
	const divisionsData = await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.get_divisions',
		args: filters
	})

}
async function getCmap() {
	const filters = getFilters()
	tempData = await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.get_cmap',
		args: filters
	})
	cmapData = tempData?.message || {}
	setupDataTable()
}

async function setupDataTable() {
	const container = document.getElementById('report-table-container')
	container.innerHTML = ""
	const filters = getFilters()
	const teachersData = await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.get_teachers',
		args: filters
	})
	container.appendChild(createTable(cmapData, teachersData.message))

}


function make_fieldgroup(parent, ddf_list) {
	fg = new frappe.ui.FieldGroup({
		"fields": ddf_list,
		"parent": parent
	});
	fg.make();

	return fg

}

function createTable(data, teachersData) {
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
	if (data)
		Object.keys(data).forEach(val => {
			data[val].forEach((row, index) => {
				const row_html = createRow(val, '231', row.division_name, row.teacher, row.plan_date, 'adad', index === 0, data[val].length, teachersData, index)
				tbody.innerHTML += (row_html)
			})
		})
	tbody.addEventListener('click', changeTeacherOnSelect)
	thead.appendChild(headerRow)
	table.appendChild(thead);

	table.appendChild(tbody);
	return table
}

function createRow(period_no, chapter_name, division, teacher, plan_date, note, first_row, rowSpan, teachersData, index) {

	if (first_row)
		return `<tr>
	<td rowspan="${rowSpan}">${period_no}</td>
	<td rowspan="${rowSpan}">${chapter_name}</td>
	<td>${division}</td>
	<td class="teacher-cell">${createSelect(teachersData, teacher, index, period_no)}</td>
	<td>${plan_date}</td>
	<td>${note}</td>
  </tr>
  `
	return `<tr>

  <td>${division}</td>
  <td class="teacher-cell">${createSelect(teachersData, teacher, index, period_no)}</td>
  <td>${plan_date}</td>
  <td>${note}</td>
</tr>

`
}

function createSelect(selectData, value, index, key) {

	return `<select data-index="${index}" data-key=${key} value="${value}"><option></option>${selectData.map((el) => (
		`<option>${el.name}</option>`
	))}</select>`
}

async function saveAssignment() {
	const filters = getFilters()
	await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.update_assignment',
		args: {
			filters: filters,
			cmap_data: cmapData
		}
	})
}