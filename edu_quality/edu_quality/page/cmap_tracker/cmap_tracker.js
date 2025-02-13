

let globalTableRef = null
let filtersRef = null
let cmapData = []
let cmapUpdate = {}
let globalPage = null
let saveButtonAdded = false
let isAdmin = false

frappe.pages['cmap-tracker'].on_page_load = async function (wrapper) {

	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'CMAP Tracker',
		single_column: true
	});
	globalPage = page

	onLoad(page)
}
frappe.pages['cmap-tracker'].refresh = async function (wrapper) {

	onLoad()
}

async function onLoad() {

	frappe.require(["/assets/edu_quality/css/cmap-tracker.css"])
	const el = globalPage.wrapper.find('.container.page-body');

	el.addClass("cmap-tracker");
	const [teachersData, acadYear, school] = await getTeachers()
	isAdmin = !teachersData
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
	// el.innerHTML = ""
	el.empty();
	filtersRef = make_fieldgroup(el, [
		{
			label: 'Academic Year',
			fieldname: 'academic_year',
			fieldtype: 'Link',
			default: acadYear || '',
			options: "Academic Year",
			change: () => filterOnChange(filtersRef.fields_dict.academic_year)
		},
		{
			label: 'School',
			fieldname: 'school',
			fieldtype: 'Link',
			default: school || '',
			options: "School",
			readonly: parseInt(!!school),
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

	const tableContainer = $('<div>').attr('id', 'report-table-container');
	const editContainer = $('<div>').attr('id', 'report-edit-container');

	el.append(tableContainer);
	el.append(editContainer);
	setupDataTable()
}
async function reInitCMAP() {
	if (cmapDataPresent()) {
		cmapData = []
		cmapUpdate = {}
		// removeSaveButton()
		await setupDataTable()
	}
}
async function filterOnChange(field) {

	// if (!cmapDataPresent()) return

	// frappe.msgprint({
	// 	title: "Warning", message: "Changing filter, will remove all the existing data"
	// })
	await reInitCMAP()


	if (filtersRef.get_value('academic_year') && filtersRef.get_value('class') && filtersRef.get_value('school') && filtersRef.get_value('unit') && filtersRef.get_value('subject')) {

		await getCmap()
		await setupDataTable()
	}
}

function cmapDataPresent() {
	return cmapData.length !== 0
}

function updateCmap(cmapName, key, value) {
	const cmap = cmapUpdate[cmapName]
	if (cmap) {
		cmap[key] = !value ? null : value
	}
	else {
		cmapUpdate[cmapName] = { [key]: !value ? null : value }
	}
}
function changeRealDateOnSelect(e) {
	const dataset = e.target.dataset
	console.log(e.target.dataset, e.target.value,)
	if (dataset.index && cmapData) {
		const cmap = cmapData[dataset.index].name
		cmapData[dataset.index].real_date = e.target.value
		updateCmap(cmap, "real_date", e.target.value)
		console.log(cmapData, cmapUpdate)
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
		method: 'edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.get_teacher_details',
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
	globalPage.set_primary_action('Save', saveTracker)
}

function removeSaveButton() {
	if (!saveButtonAdded) return
	globalPage.clear_primary_action()
}

async function setupDataTable() {
	const container = document.getElementById('report-table-container')
	container.innerHTML = ""

	container.appendChild(createTable(cmapData))
	$(function () {
		$('[data-toggle="tooltip"]').tooltip({ trigger: 'hover focus click manual' })

	})

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
	{ textContent: 'Period No.', className: "period-no-header", colSpan: 1 },
	{ textContent: 'Chapter Name', colSpan: 2 },
	{ textContent: 'Products', colSpan: 1 },
	{ textContent: 'Broadcast', colSpan: 1 },
	{ textContent: 'Parent Note', colSpan: 1 },
	{ textContent: 'Classwork', colSpan: 1 },
	{ textContent: 'Homework', colSpan: 1 },
	{ textContent: 'Material Required', colSpan: 1 },


	{ textContent: 'Plan Date' },
	{ textContent: 'Real Date' },



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
			const row_html = createRow(row.period, row.chapter_name, generateProductList(row.products), row.broadcast, row.parent_note, row.class_work, row.home_work, row.material_required, row.division, row.teacher, row.plan_date, row.real_date, index === 0, 0, index)
			tbody.innerHTML += (row_html)
		})


	tbody.addEventListener('change', changeRealDateOnSelect)

	thead.appendChild(headerRow)
	table.appendChild(thead);

	table.appendChild(tbody);
	return table
}

function generateProductList(products) {
	const generatedProducts = products && products.map(el => `<div style="display:flex;gap:4px;"><a target="__blank" href="${el.custom_product_url}">${el.item_code} </a><a target="__blank" href="/app/item/${el.item_code}"><i class="fa fa-comment" aria-hidden="true"></i></a></div>`).join('')
	return `<div class="products-list">${generatedProducts}</div>`
}
function createRow(period_no, chapter_name, products, broadcast, parent_note, class_work, home_work, material_required, division, teacher, plan_date, real_date, first_row, rowSpan, index) {


	return `<tr>
	<td >${period_no}</td>
	<td colspan="2">${chapter_name}</td>
	<td>${products}</td>
	<td  data-toggle="tooltip" data-placement="top" title="${broadcast}"><i class="fa fa-file" aria-hidden="true"></i></td>
	<td data-toggle="tooltip" data-placement="top" title="${parent_note}"><i class="fa fa-file" aria-hidden="true"></i></td>
	<td  data-toggle="tooltip" data-placement="top" title="${class_work}"><i class="fa fa-file" aria-hidden="true"></i></td>
	<td  data-toggle="tooltip" data-placement="top" title="${home_work}"><i class="fa fa-file" aria-hidden="true"></i></td>
<td data-toggle="tooltip" data-placement="top" title="${material_required}"><i class="fa fa-file" aria-hidden="true"></i></td>

	<td>${plan_date || "No Date"}</td>
	<td class="real-date-cell">${createDatePicker(real_date, index)}</td>
  </tr>
		`


}

function createDatePicker(value, index) {

	return `<input type="date" ${!isAdmin && value ? "disabled" : ""} value=${value} data-index="${index}" max="${getMaxDate()}" />`
}

async function saveTracker() {
	const filters = getFilters()
	await frappe.call({
		method: 'edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.update',
		args: {
			filters: filters,
			cmap_data: cmapUpdate
		}
	})
	frappe.show_alert({
		message: __('Saved'),
		indicator: 'green'
	}, 5);
	cmapUpdate = {}
	await reInitCMAP()
	await getCmap()
	await setupDataTable()
}

function getMaxDate() {
	const today = new Date();
	const day = today.getDate();
	const month = today.getMonth() + 1; // Months are zero-based
	const year = today.getFullYear();
	return `${year}-${month.toString().padStart(2, '0')}-${day}`
}