// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
let criteriasChanged = []

function throttle(func, limit) {
	let lastFunc;
	let lastRan;
	return function () {
		const context = this;
		const args = arguments;
		if (!lastRan) {
			func.apply(context, args);
			lastRan = Date.now();
		} else {
			clearTimeout(lastFunc);
			lastFunc = setTimeout(function () {
				if ((Date.now() - lastRan) >= limit) {
					func.apply(context, args);
					lastRan = Date.now();
				}
			}, limit - (Date.now() - lastRan));
		}
	}
}

function debounce(func, delay) {
	let debounceTimer;
	return function () {
		const context = this;
		const args = arguments;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => func.apply(context, args), delay);
	};
}

const throttledAutoSave = throttle(function () {
	saveCall(true);

}, 6000)

function changeMarksData(value, columnId, rowIndex, maximumScore, scoring_type) {
	const inputEl = document.querySelector(`input[column='${columnId}'][data-rowindex='${rowIndex}']`);

	if (inputEl && inputEl.dataset && inputEl.dataset.docstatus === "1") {
		const message = `
        <div>    
            <p>You Have Entered Marks in a submitted result, do you want to cancel it for processing ?</p>
        </div>`;

		frappe.confirm(__(message), async () => {
			console.log(rowIndex)
			const ref_no = frappe.query_report.data[rowIndex].ref_no
			await cancelResult(columnId, ref_no)

		});

	}

	if (Number(value.value) > Number(maximumScore) && scoring_type == "Marks") {

		inputEl.value = "";
		writeMarks(rowIndex, columnId, "");
		return;
	}

	writeMarks(rowIndex, columnId, value.value)


	throttledAutoSave()
}
function writeMarks(rowIndex, columnId, value) {
	if (frappe.query_report.data[rowIndex][columnId]) {
		frappe.query_report.data[rowIndex][columnId]["content"] = value;
	}
	else {
		frappe.query_report.data[rowIndex][columnId] = { "content": value }
	}

	criteriasChanged.push({ "ref_no": frappe.query_report.data[rowIndex]["ref_no"], "student_name": frappe.query_report.data[rowIndex]["student_name"], [columnId]: frappe.query_report.data[rowIndex][columnId] })

}
function getNextElement(rowIndex, colIndex) {
	const maxRows = frappe.query_report.data.length;
	const maxColumns = frappe.query_report.columns.length;

	let nextRowIndex = parseInt(rowIndex) + 1;
	let nextColIndex = parseInt(colIndex);

	if (nextRowIndex >= maxRows) {
		nextRowIndex = 0;
		if (nextColIndex + 1 <= maxColumns) {
			nextColIndex += 1;
		} else {
			nextColIndex = 3;
		}
	}

	return document.querySelector(`input[data-rowindex="${nextRowIndex}"][data-colindex="${nextColIndex}"]`);
}

function handleKeyDownEvent(event) {
	if (event.key === 'Tab' || event.key === "Enter") {
		event.preventDefault();

		const { colindex, rowindex } = event.target.dataset;
		const nextElement = getNextElement(rowindex, colindex);

		if (nextElement) {
			nextElement.focus();
			nextElement.select()
		}
	}
}

function initializeKeyListener() {
	document.addEventListener('keydown', handleKeyDownEvent);
}

function createInputElement(value, column, row, docstatus) {
	const isRed = String(value).toLowerCase() === "-";
	const classes = [""]
	const inputValue = isRed ? "style='background-color:var(--red-300);'" : "";
	if (isRed) {
		classes.push("absent-input")
	}
	if (docstatus == 1) {
		classes.push("submitted-input")
	}
	return `<input type="text" data-docstatus="${docstatus || 0}" data-colindex="${column.colIndex}" class="${classes.join(" ")}" column="${column.fieldname}" data-rowindex="${row && row[0] && row[0].rowIndex}" max="${column.maximum_score}" maximum-score="${column.maximum_score}" value="${value}" oninput="changeMarksData(this, '${column.id}', '${row[0]?.rowIndex}', '${column.maximum_score}','${column.scoring_type}')" />`;
}

function formatter(value, row, column, data, defaultFormatter) {
	value = defaultFormatter(value, row, column, data);
	const values = data[column.fieldname]
	const docstatus = values && values.docstatus
	if (column.is_criteria) {
		value = createInputElement(value, column, row, docstatus);
	}

	return value;
}
async function saveCall(autoSave = false) {
	const filters = {};
	console.log(criteriasChanged)
	frappe.query_report.filters.forEach(filter => {
		filters[filter.fieldname] = frappe.query_report.get_filter_value(filter.fieldname);
	});
	let data = frappe.query_report.data
	if (autoSave) {
		data = criteriasChanged
	}
	await frappe.call({
		"method": "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.do_mark_entry",
		args: {
			data: data,
			filters: filters,
		}
	});
	criteriasChanged = []
	frappe.show_alert({
		message: __('<i class="fa fa-save"></i>'),
		indicator: 'green'
	}, 2);
}
const cancelResult = debounce(async (field_name, ref_no) => {
	const filters = {};

	frappe.query_report.filters.forEach(filter => {
		filters[filter.fieldname] = frappe.query_report.get_filter_value(filter.fieldname);
	});
	await frappe.call({
		"method": "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.cancel_result",
		args: {
			ref_no: ref_no,
			field_name: field_name,
			filters: filters,
		}
	});

	frappe.show_alert({
		message: __(`Cancelled for ${ref_no} successfully`),
		indicator: 'green'
	}, 2);
}, 1000)

function onload(report) {
	initializeKeyListener();

	frappe.require(["/assets/edu_quality/css/mark-entry-tool.css"]);
	report.page.parent.classList.add("mark-entry-tool-report");
	addNote()
	report.page.add_inner_button(__('Save Marks Entry'), () => {
		const message = `
        <div>    
            <p>Are you sure you want to Save Marks Entered?</p>
        </div>`;

		frappe.confirm(__(message), async () => {
			await saveCall()

		});
	});
	report.page.add_inner_button(__('Process Result'), () => {
		const message = `
        <div>    
            <p>Are you sure you want to Leave this page and go to exam processing?</p>
        </div>`;

		frappe.confirm(__(message), async () => {
			goToProcessing()

		});
	});
}

function goToProcessing() {
	const academic_year = frappe.query_report.get_filter_value("academic_year");
	const school = frappe.query_report.get_filter_value("school");
	const program = frappe.query_report.get_filter_value("program");
	const exam = frappe.query_report.get_filter_value("assessment_group");

	frappe.set_route("process-exam-result", { academic_year, school, program, exam })
}
function addNote() {
	const noteContainer = frappe.query_report.parent.querySelector('.page-head .container');
	const noteContainerDiv = document.createElement("div")
	if (noteContainer.querySelector(".note-container")) {
		return
	}
	noteContainerDiv.classList.add("note-container")
	noteContainerDiv.innerHTML = `
	<div class="form-message blue my-0">
	<ul>
	<li>Non Submitted Exam Config Subjects inside an Exam Configuration and their subject components won't show up for marking</li>
	<li>Use - for marking student as absent</li>
	<li>Empty Columns will be marked as absent automatically, on first save</li>
	</ul>
	</div>`
	noteContainer.appendChild(noteContainerDiv)
}

frappe.query_reports["Marks Entry Tool"] = {
	"filters": [
		{
			"fieldname": "academic_year",
			"fieldtype": "Link",
			"options": "Academic Year",
			"label": "Academic Year",
			"get_query": "edu_quality.public.py.utils.academic_year_query"
		},
		{
			"fieldname": "school",
			"fieldtype": "Link",
			"options": "School",
			"label": "School"
		},
		{
			"fieldname": "program",
			"label": __("Class"),
			"fieldtype": "Link",
			"options": "Program",
			"reqd": 1,
			"get_query": function (txt) {
				const school = frappe.query_report.get_filter_value("school");
				return { filters: { "school": school } };
			}
		},
		{
			"fieldname": "assessment_group",
			"label": __("Assessment Group"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Assessment Group",
			"get_query": function (txt) {
				const school = frappe.query_report.get_filter_value("school");
				const academic_year = frappe.query_report.get_filter_value("academic_year");
				const program = frappe.query_report.get_filter_value("program");
				return { filters: { "custom_is_composite": 0, "custom_academic_year": academic_year, "custom_school": school, "custom_program": program } };
			}
		},
		{
			"fieldname": "division",
			"label": __("Division"),
			"fieldtype": "Link",
			"options": "Student Group",
			"reqd": 1,
			"get_query": function (txt) {
				const program = frappe.query_report.get_filter_value("program");
				const academic_year = frappe.query_report.get_filter_value("academic_year");
				return { filters: { "program": program, academic_year: academic_year } };
			}
		}
	],
	"formatter": formatter,
	"onload": onload,
};