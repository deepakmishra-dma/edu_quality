let globalTableRef = null
let filtersRef = null
let cmapData = {}
let globalPage = null
let saveButtonAdded = false

frappe.pages['cmap-assignment-tool'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'CMAP Assignment Tool',
		single_column: true
	});
	globalPage = page
	frappe.require(["/assets/edu_quality/css/cmap-assignment-tool.css"])
	const el = document.querySelector('.container.page-body')
	el.classList.add("cmap-assignment-tool")

	filtersRef = make_fieldgroup(el, [
		{
			label: 'Academic Year',
			fieldname: 'academic_year',
			fieldtype: 'Link',
			options: "Academic Year",
			change: () => changeFilterWarning(filtersRef.fields_dict.academic_year)
		},
		{
			label: 'Class',
			fieldname: 'class',
			fieldtype: 'Link',
			options: "Class Type",
			change: () => changeFilterWarning(filtersRef.fields_dict.class)
		}, {
			label: 'Subject',
			fieldname: 'subject',
			fieldtype: 'Link',
			options: "Course",
			change: () => changeFilterWarning(filtersRef.fields_dict.subject)
		}, {
			label: 'School',
			fieldname: 'school',
			fieldtype: 'Link',
			options: "School",
			change: () => changeFilterWarning(filtersRef.fields_dict.school)
		}, {
			label: 'Unit',
			fieldname: 'unit',
			fieldtype: 'Select',
			options: ["1", "2", "3", "4"],
			change: () => changeFilterWarning(filtersRef.fields_dict.unit)
		},
	])


	// page.add_inner_button('Fetch', () => {

	// 	getDivisions()
	// 	getCmap()

	// })
	const tableContainer = document.createElement('div')
	const editContainer = document.createElement('div')
	editContainer.id = 'report-edit-container'
	tableContainer.id = 'report-table-container'

	el.appendChild(tableContainer)
	el.appendChild(editContainer)
	setupDataTable()

}
function editMode() {
	if (!cmapDataPresent()) {
		return frappe.msgprint({
			title: __('Error'),
			message: __('No Data'),

		})
	}

	const d = new frappe.ui.Dialog({
		title: 'Bulk Edit',
		fields: [{
			label: 'Division',
			fieldname: 'division',
			fieldtype: 'Link',
			options: "Student Group",
			get_query: () => {
				return {

					"filters": {
						"academic_year": filtersRef.get_value('academic_year'),
						"program": `${filtersRef.get_value('class')}-${filtersRef.get_value('school')}`
					}

				}
			}
		},
		{
			label: 'Teacher',
			fieldname: 'teacher',
			fieldtype: 'Link',
			options: "Instructor",
			get_query: () => {
				return {

					"filters": {
						"custom_school": filtersRef.get_value('school'),

					}

				}
			}
		},
		],
		size: "small",
		primary_action_label: "Apply",

		primary_action: () => { changeCmapDataBulk(d); d.hide() }
	},
	)

	d.show()
	// const d = make_fieldgroup(container, [
	// 	,
	// 	{ label: 'Save', fieldtype: "Button", click: () => saveAssignment() }

	// ])
}
async function changeFilterWarning(field) {

	// if (!cmapDataPresent()) return

	// frappe.msgprint({
	// 	title: "Warning", message: "Changing filter, will remove all the existing data"
	// })
	if (cmapDataPresent()) {
		cmapData = {}
		removeBulkEdit()
		// removeSaveButton()
		await setupDataTable()
	}
	console.log(filtersRef.get_value('academic_year'), filtersRef.get_value('class'), filtersRef.get_value('school'), filtersRef.get_value('unit'), filtersRef.get_value('subject'))
	if (filtersRef.get_value('academic_year') && filtersRef.get_value('class') && filtersRef.get_value('school') && filtersRef.get_value('unit') && filtersRef.get_value('subject')) {
		await getDivisions()
		await getCmap()
		await setupDataTable()
	}
}

function cmapDataPresent() {
	return Object.keys(cmapData).length !== 0
}
function changeCmapDataBulk(fieldGroup) {
	const division = fieldGroup.fields_dict["division"].value
	const teacher = fieldGroup.fields_dict["teacher"].value

	Object.keys(cmapData).forEach(key => cmapData[key].forEach((values, index) => {

		if (values.division_name == division) {
			cmapData[key][index] = { ...cmapData[key][index], teacher }

		}

	}))
	addSaveButton()
	setupDataTable()
}

function changeTeacherOnSelect(e) {
	const dataset = e.target.dataset

	if (dataset.index && dataset.key && cmapData) {
		cmapData[dataset.key][dataset.index].teacher = e.target.value

		// setupDataTable(cmapData)
	}
	addSaveButton()
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
	addBulkEdit()
	await setupDataTable()
}
function addBulkEdit() {
	if (cmapDataPresent())
		globalPage.add_inner_button('Bulk Edit', editMode)
}
function removeBulkEdit() {
	globalPage.remove_inner_button('Bulk Edit')
}

function addSaveButton() {
	if (!cmapDataPresent() || saveButtonAdded) return
	saveButtonAdded = 1
	globalPage.set_primary_action('Save', saveAssignment)
}

function removeSaveButton() {
	if (!saveButtonAdded) return
	globalPage.clear_primary_action()
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
const headers = [
	{ textContent: 'Peroid No.', colSpan: 1 },
	{ textContent: 'Chapter Name', colSpan: 2 },
	{ textContent: 'Division' },
	{ textContent: 'Teacher' },
	{ textContent: 'Plan Date' },
	{ textContent: 'Note' }
];

function createTable(data, teachersData) {
	if (!cmapDataPresent()) {
		const div = document.createElement("div")
		div.textContent = "No Data/Select The Correct Filters and then press Fetch, to display assignments"
		div.className = "no-content"
		return div
	}

	const table = document.createElement('table');
	const thead = document.createElement('thead')
	const tbody = document.createElement('tbody')
	const headerRow = document.createElement('tr');

	headers.forEach(header => {
		const headerCell = document.createElement('th');
		headerCell.textContent = header.textContent;
		if (header.className) {
			headerCell.className = (header.className);
		}
		if (header.colSpan) {
			headerCell.colSpan = header.colSpan;
		}
		headerRow.appendChild(headerCell);
	});

	if (data)
		Object.keys(data).forEach(val => {
			data[val].forEach((row, index) => {
				const row_html = createRow(val, row.products && row.products.join(','), row.division_name, row.teacher, row.plan_date, '', index === 0, data[val].length, teachersData, index)
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
	<td rowspan="${rowSpan}" colspan="2">${chapter_name}</td>
	<td>${division}</td>
	<td class="teacher-cell">${createSelect(teachersData, teacher, index, period_no)}</td>
	<td>${plan_date || "No Date"}</td>
	<td>${note || "No Note"}</td>
  </tr>
  `
	return `<tr>

  <td>${division}</td>
  <td class="teacher-cell">${createSelect(teachersData, teacher, index, period_no)}</td>
  <td>${plan_date || "No Date"}</td>
  <td>${note || "No Note"}</td>
</tr>

`
}

function createSelect(selectData, value, index, key) {

	return `<select data-index="${index}" data-key=${key} ><option></option>${selectData.map((el) => (
		`<option ${el.name === value ? `selected="selected"` : ''} value="${el.name}">${el.name}</option>`
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
	frappe.show_alert({
		message: __('Saved'),
		indicator: 'green'
	}, 5);
}