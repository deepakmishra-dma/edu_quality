let globalTableRef = null
let filtersRef = null
let transportData = []

frappe.pages['transport-drop-page'].on_page_load = async function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Drop',
		single_column: true
	});
	wrapper.classList.add("drop-transport")
	globalPage = page
	await onLoad()
}

function getBusDetails() {



}

function onViewClicked() {
	setupViewTable()
}





async function onLoad() {

	frappe.require(["/assets/edu_quality/css/drop-transport.css"])

	const el = globalPage.wrapper.find('.container.page-body');

	el.add("drop-transport")

	filtersRef = make_fieldgroup(el, [
		{
			label: 'Bus No',
			fieldname: 'bus_no',
			fieldtype: 'Data',

		},
		{
			label: "View",
			fieldname: "view_button",
			fieldtype: "Button",
			click: () => {
				console.log('hah')
				onViewClicked()
			}
		}
	])

	const tableContainer = $('<div>').attr('id', 'report-table-container');
	el.append(tableContainer);
}



function transportDataPresent() {
	return transportData.length !== 0
}

function updateTransport(cmapName, key, value) {
	const cmap = cmapUpdate[cmapName]
	if (cmap) {
		cmap[key] = value
	}
	else {
		cmapUpdate[cmapName] = { [key]: value }
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






async function setupViewTable() {
	const container = document.getElementById('report-table-container')
	const subContainer = document.createElement('div')
	container.innerHTML = ""
	subContainer.innerHTML = ""
	container.appendChild(createLegend())
	const label = document.createElement("label")
	label.innerText = `Student Details (${transportData?.length || 0})`
	container.appendChild(label)

	subContainer.appendChild(createTable(transportData))
	$(function () {
		$('[data-toggle="tooltip"]').tooltip({ trigger: 'hover focus click manual' })

	})
	container.appendChild(subContainer)
	const qrButton = document.createElement('button')
	qrButton.classList.add('qr-code-btn', "btn", "btn-primary", "btn-sm", "primary-action")
	qrButton.innerHTML = `<div style ="height:24px;width:24px" ><i style ="font-size:24px;height:24px;width:24px" class="fa fa-qrcode" aria-hidden="true"></i></div>Scan QR`
	container.appendChild(qrButton)
}

const legendsBgHash = {
	"early_pickup": "ep-bg",
	"late_drop": "ld-bg",
	"onboard": "ob-bg",
	"absent": "ab-bg"
}
function createLegend() {
	const legends = [
		{ label: "Early Pickup", "class": "ep-bg" },
		{ label: "Late Drop", "class": "ld-bg" },
		{ label: "Onboard", "class": "ob-bg" },
		{ label: "Absent", "class": "ab-bg" }
	]
	const legendContainer = document.createElement('div')
	legendContainer.classList.add("legend-container")

	const generatedLegends = legends.map((el) => {
		return `<div class="legend"><div class="${el.class}"></div><div>${el.label}</div></div>`
	}).join('')
	legendContainer.innerHTML = generatedLegends
	return legendContainer
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
	{ textContent: 'Photo', className: "period-no-header", colSpan: 1 },
	{ textContent: 'Student', colSpan: 2 },
	{ textContent: 'Address', colSpan: 2 },
	{ textContent: '', colSpan: 1 },
];
function studentCheckChange() {

}

function createTable(data) {
	// if (!transportDataPresent()) {
	// 	const div = document.createElement("div")

	// 	return div
	// }

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
	data = [{ "address": "Lorem ipsum test", "student": "Aryan", "photo": "https://thumbs.dreamstime.com/b/pet-animal-cute-white-cat-turkish-ankara-141360014.jpg", drop_type: "early_pickup" },
	{ "address": "Lorem ipsum test", "student": "Aryan", "photo": "https://thumbs.dreamstime.com/b/pet-animal-cute-white-cat-turkish-ankara-141360014.jpg", drop_type: "absent" },
	{ "address": "Lorem ipsum test", "student": "Aryan", "photo": "https://thumbs.dreamstime.com/b/pet-animal-cute-white-cat-turkish-ankara-141360014.jpg", drop_type: "late_drop" },
	{ "address": "Lorem ipsum test", "student": "Aryan", "photo": "https://thumbs.dreamstime.com/b/pet-animal-cute-white-cat-turkish-ankara-141360014.jpg", drop_type: "onboard" },
	{ "address": "Lorem ipsum test", "student": "Aryan", "photo": "https://thumbs.dreamstime.com/b/pet-animal-cute-white-cat-turkish-ankara-141360014.jpg", drop_type: "onboard" },
	{ "address": "Lorem ipsum test", "student": "Aryan", "photo": "https://thumbs.dreamstime.com/b/pet-animal-cute-white-cat-turkish-ankara-141360014.jpg", drop_type: "onboard" },
	{ "address": "Lorem ipsum test", "student": "Aryan", "photo": "https://thumbs.dreamstime.com/b/pet-animal-cute-white-cat-turkish-ankara-141360014.jpg", drop_type: "onboard" }]
	if (data)

		data.forEach((row, index) => {
			const row_html = createRow(row.photo, row.student, row.address, "id", row.drop_type, index === 0, 0, index)
			tbody.innerHTML += (row_html)
		})


	tbody.addEventListener('click', studentCheckChange)

	thead.appendChild(headerRow)
	table.appendChild(thead);

	table.appendChild(tbody);
	return table
}


function createRow(photo, student, address, student_id, drop_type) {
	legendsBgHash

	return `<tr class="${legendsBgHash[drop_type]}">
	<td ><img width="3rem" height="3rem" src="${photo}"/></td>
	<td colspan="2">${student}</td>
	<td colspan="2"${address}</td>
	<td data-check="true" data-index="student-id">${createCheck(student_id)}</td>
  </tr>
		`


}

function createCheck(value, index) {

	return `<input type="checkbox" value=${value} data-index="${value}"  />`
}


