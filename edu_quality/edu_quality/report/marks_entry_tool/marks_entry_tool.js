// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
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
	saveCall();

}, 6000)

function changeMarksData(value, columnId, rowIndex, maximumScore) {
	if (Number(value.value) > Number(maximumScore)) {
		const inputEl = document.querySelector(`input[column='${columnId}'][data-rowindex='${rowIndex}']`);
		inputEl.value = "";
		frappe.query_report.data[rowIndex][columnId] = "";
		return;
	}
	frappe.query_report.data[rowIndex][columnId] = value.value;

	throttledAutoSave()
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
	if (event.key === 'Tab') {
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

function createInputElement(value, column, row) {
	const isRed = String(value).toLowerCase() === "ab";
	const inputValue = isRed ? "style='background-color:var(--red-300);'" : "";

	return `<input type="text" data-colindex="${column.colIndex}" ${inputValue} column="${column.fieldname}" data-rowindex="${row[0]?.rowIndex}" max="${column.maximum_score}" maximum-score="${column.maximum_score}" value="${value}" oninput="changeMarksData(this, '${column.id}', '${row[0]?.rowIndex}', '${column.maximum_score}')" />`;
}

function formatter(value, row, column, data, defaultFormatter) {
	value = defaultFormatter(value, row, column, data);

	if (column.is_criteria) {
		value = createInputElement(value, column, row);
	}

	return value;
}
async function saveCall() {
	const filters = {};

	frappe.query_report.filters.forEach(filter => {
		filters[filter.fieldname] = frappe.query_report.get_filter_value(filter.fieldname);
	});

	await frappe.call({
		"method": "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.do_mark_entry",
		args: {
			data: frappe.query_report.data,
			filters: filters,
		}
	});

	frappe.show_alert({
		message: __('Saved'),
		indicator: 'green'
	}, 2);
}
function onload(report) {
	initializeKeyListener();

	frappe.require(["/assets/edu_quality/css/mark-entry-tool.css"]);
	report.page.parent.classList.add("mark-entry-tool-report");

	report.page.add_inner_button(__('Save Marks Entry'), () => {
		const message = `
        <div>    
            <p>Are you sure you want to Save Marks Entered?</p>
        </div>`;

		frappe.confirm(__(message), async () => {
			await saveCall()

		});
	});
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