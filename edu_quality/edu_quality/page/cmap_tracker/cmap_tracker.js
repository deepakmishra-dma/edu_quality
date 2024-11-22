

let globalTableRef = null
let filtersRef = null
let cmapData = []
let globalPage = null
let saveButtonAdded = false

frappe.pages['cmap-tracker'].on_page_load = async function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'CMAP Tracker',
		single_column: true
	});
	globalPage = page
	frappe.require(["/assets/edu_quality/css/cmap-tracker.css"])
	const el = document.querySelector('.container.page-body')
	el.classList.add("cmap-tracker")
	const teachersData = await getTeachers()
	const teacherFilter = !teachersData ? [{
		label: 'Teacher',
		fieldname: 'teacher',
		fieldtype: 'Link',
		options: "Instructor",
		readonly: teachersData,

		get_query: () => {
			return {
				"filters": {

					"custom_school": filtersRef.get_value('school'),

				}

			}
		},
		change: () => filterOnChange(filtersRef.fields_dict.school)
	}] : [];

	filtersRef = make_fieldgroup(el, [
		{
			label: 'Academic Year',
			fieldname: 'academic_year',
			fieldtype: 'Link',
			options: "Academic Year",
			change: () => filterOnChange(filtersRef.fields_dict.academic_year)
		},
		{
			label: 'School',
			fieldname: 'school',
			fieldtype: 'Link',
			options: "School",
			change: () => filterOnChange(filtersRef.fields_dict.school)
		},
		{
			label: 'Class',
			fieldname: 'class',
			fieldtype: 'Link',
			options: "Class Type",

			change: () => filterOnChange(filtersRef.fields_dict.class)
		},
		{
			label: 'Division',
			fieldname: 'division',
			fieldtype: 'Link',
			options: "Student Group",
			get_query: () => {
				return {
					"filters": {
						"program": filtersRef.get_value('school'),
						"academic_year": filtersRef.get_value('academic_year'),
						"program": `${filtersRef.get_value('class')}-${filtersRef.get_value('school')}`
					}

				}
			},
			change: () => filterOnChange(filtersRef.fields_dict.division)
		},
		{
			label: 'Subject',
			fieldname: 'subject',
			fieldtype: 'Link',
			options: "Course",
			change: () => filterOnChange(filtersRef.fields_dict.subject)
		},
		...teacherFilter,
		{
			label: 'Unit',
			fieldname: 'unit',
			fieldtype: 'Select',
			options: ["1", "2", "3", "4"],
			change: () => filterOnChange(filtersRef.fields_dict.unit)
		},
	])


	// page.add_inner_button('Fetch', () => {


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

async function filterOnChange(field) {

	// if (!cmapDataPresent()) return

	// frappe.msgprint({
	// 	title: "Warning", message: "Changing filter, will remove all the existing data"
	// })
	if (cmapDataPresent()) {
		cmapData = []

		// removeSaveButton()
		await setupDataTable()
	}
	console.log(filtersRef.get_value('academic_year') && filtersRef.get_value('class') && filtersRef.get_value('school') && filtersRef.get_value('unit') && filtersRef.get_value('subject'))
	if (filtersRef.get_value('academic_year') && filtersRef.get_value('class') && filtersRef.get_value('school') && filtersRef.get_value('unit') && filtersRef.get_value('subject')) {

		await getCmap()
		await setupDataTable()
	}
}

function cmapDataPresent() {
	return cmapData.length !== 0
}


function changeRealDateOnSelect(e) {
	const dataset = e.target.dataset
	console.log(dataset.index, 'haha')
	if (dataset.index && cmapData) {
		cmapData[dataset.index].real_date = e.target.value


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

async function getTeachers() {
	const teacherData = await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.calculate_teacher_value',
		args: { value_for_admin: "" }
	})
	return teacherData?.message
}
async function getCmap() {
	const filters = getFilters()
	tempData = await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.get_cmap',
		args: filters
	})
	cmapData = tempData?.message || []

	await setupDataTable()
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



	container.appendChild(createTable(cmapData))

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
	{ textContent: 'Period No.', colSpan: 1 },
	{ textContent: 'Chapter Name', colSpan: 2 },
	{ textContent: 'Products', colSpan: 1 },
	{ textContent: 'Division' },
	{ textContent: 'Plan Date' },
	{ textContent: 'Real Date' },
	{ textContent: 'Teacher' },

];

function createTable(data) {
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

		data.forEach((row, index) => {
			const row_html = createRow(row.period, row.chapter_name, row.products && row.products.map(el => `<a target="__blank" href="${el.custom_product_url}">${el.item_code}</a>`).join(','), row.division, row.teacher, row.plan_date, row.real_date, index === 0, 0, index)
			tbody.innerHTML += (row_html)
		})


	tbody.addEventListener('change', changeRealDateOnSelect)
	thead.appendChild(headerRow)
	table.appendChild(thead);

	table.appendChild(tbody);
	return table
}

function createRow(period_no, chapter_name, products, division, teacher, plan_date, real_date, first_row, rowSpan, index) {


	return `<tr>
	<td >${period_no}</td>
	<td colspan="2">${chapter_name}</td>
	<td>${products}</td>
	<td>${division}</td>
	<td>${plan_date || "No Date"}</td>
	<td class="real-date-cell">${createDatePicker(real_date, index)}</td>
	<td>${teacher}</td>
  </tr>
  `


}

function createDatePicker(value, index) {

	return `<input type="date" value=${value} data-index="${index}"/>`
}

async function saveAssignment() {
	const filters = getFilters()
	await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.update',
		args: {
			filters: filters,
			cmap_data: cmapData
		}
	})
}