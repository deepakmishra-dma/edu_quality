// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
let criteriasChanged = {}

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
const fetchSaveOnlyOnce = function () {
	let loading = false
	return async function () {
		if (loading) return
		loading = true
		await saveCall(true);
		loading = false
	}
}

// const throttledAutoSave = throttle(fetchSaveOnlyOnce(), 6000)

function changeMarksData(value, columnId, rowIndex, maximumScore, scoring_type, columnIndex) {
	const inputEl = document.querySelector(`input[column='${columnId}'][data-rowindex='${rowIndex}']`);



	if (Number(value.value) > Number(maximumScore) && scoring_type == "Marks") {

		inputEl.value = "";
		writeMarks(rowIndex, columnId, "", columnIndex);
		return;
	}

	writeMarks(rowIndex, columnId, value.value, columnIndex)


	// throttledAutoSave()
}
function updateCell(value, columnId, rowIndex, maximumScore, scoring_type, columnIndex) {
	frappe.query_report.datatable.bodyRenderer.cellmanager.updateCell(columnIndex, rowIndex, value.value, true)
}

function writeMarks(rowIndex, columnId, value, columnIndex) {
	if (frappe.query_report.data[rowIndex][columnId]) {
		frappe.query_report.data[rowIndex][columnId] = value;
	}
	else {
		frappe.query_report.data[rowIndex][columnId] = value
	}
	const { ref_no,
		roll_no,
		student_name,
		assessment_criteria,
		assessment_plan,
		question,
		feature,
		parent_question
	} = frappe.query_report.data[rowIndex]

	const payload = {
		ref_no: ref_no,
		roll_no: roll_no,
		student_name: student_name,
		assessment_criteria: assessment_criteria,
		assessment_plan: assessment_plan,
		question: question,
		parent_question: parent_question,
		feature: feature,
		[columnId]: frappe.query_report.data[rowIndex][columnId]
	}

	if (!ref_no && !student_name) {
		if (!criteriasChanged[`${question} ${assessment_plan}`])
			criteriasChanged[`${question} ${assessment_plan}`] = {};

		Object.assign(criteriasChanged[`${question} ${assessment_plan}`], payload);
	}

	else if (ref_no && student_name) {
		if (!criteriasChanged[ref_no])
			criteriasChanged[ref_no] = {};

		Object.assign(criteriasChanged[ref_no], payload);
	}

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

	nextEl = document.querySelector(`input[data-rowindex="${nextRowIndex}"][data-colindex="${nextColIndex}"]`)

	if (nextEl && nextEl.dataset.docstatus == 1)
		return getNextElement(nextRowIndex, nextColIndex)
	return nextEl

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

function createInputElement(value, column, row, docstatus, onlineAssess) {
	const isRed = String(value).toLowerCase() === "-";
	const classes = [""]
	const inputValue = isRed ? "style='background-color:var(--red-300);'" : "";
	let inputDisabled = false
	if (isRed) {
		classes.push("absent-input")
	}
	if (docstatus == 1) {
		inputDisabled = true
		classes.push("submitted-input")
	}
	if (onlineAssess == 1) {
		classes.push("assess-input")
	}

	return `<input type="text" ${inputDisabled ? "disabled='true'" : ""} data-docstatus="${docstatus || 0}" data-colindex="${column.colIndex - 1}" class="${classes.join(' ')}" column="${column.fieldname}" data-rowindex="${row && row[0] && row[0].rowIndex}" max="${column.maximum_score}" maximum-score="${column.maximum_score}" value="${value}" oninput="changeMarksData(this, '${column.id}', '${row[0]?.rowIndex}', '${column.maximum_score}','${column.scoring_type}',${column.colIndex})" onfocusout="updateCell(this, '${column.id}', '${row[0]?.rowIndex}', '${column.maximum_score}','${column.scoring_type}',${column.colIndex})" />`;
}

function formatter(value, row, column, data, defaultFormatter) {

	value = defaultFormatter(value, row, column, data);
	const values = data[column.fieldname + "_is_extra"]
	
	const docstatus = (values && values.docstatus) || data.docstatus
	const onlineAssess = (values && values.online_assess) || data.online_assess

	if (column.is_criteria) {
		value = createInputElement(value, column, row, docstatus, onlineAssess);
	}

	return value;
}

function switchToNormal() {

	const filters = frappe.query_report.get_filter_values();

	// Iterate through each filter and clear its value

	frappe.query_report.set_filter_value("mode", '');
	frappe.query_report.set_filter_value("ref_no", '');


	frappe.query_report.refresh();
}
async function saveCall(autoSave = false) {
	const filters = {};

	frappe.query_report.filters.forEach(filter => {
		filters[filter.fieldname] = frappe.query_report.get_filter_value(filter.fieldname);
	});
	let data = frappe.query_report.data
	if (autoSave) {
		data = criteriasChanged
	}
	console.log(criteriasChanged)
	await frappe.call({
		"method": "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.do_mark_entry",
		args: {
			data: Object.keys(criteriasChanged).map((key) => {
				return criteriasChanged[key]
			}),
			filters: filters,
		}
	});
	criteriasChanged = {}
	frappe.show_alert({
		message: __('<i class="fa fa-save"></i>'),
		indicator: 'green'
	}, 2);
}

function sendMarks(assessment_group, division) {

	frappe.call({
		method: "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.send_marks",
		args: {
			assessment_group: assessment_group,
			division: division
		},
		callback: function (r) {
			if (r.message) {
				frappe.show_alert({
					message: __('Marks Sending Queued Successfully'),
					indicator: 'green'
				}, 2);
			} else {
				frappe.show_alert({
					message: __('Marks Sending Failed'),
					indicator: 'red'
				}, 2);
			}
		}
	});
}

const cancelResult = debounce(async (ref_nos) => {
	const filters = {};

	frappe.query_report.filters.forEach(filter => {
		filters[filter.fieldname] = frappe.query_report.get_filter_value(filter.fieldname);
	});
	await frappe.call({
		"method": "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.cancel_result_rows",
		args: {
			ref_nos: ref_nos,
			filters: filters,
		}
	});
	frappe.query_report.refresh()
	frappe.show_alert({
		message: __(`Cancelled for ${ref_nos.join(",")} successfully`),
		indicator: 'green'
	}, 2);
}, 1000)
function checkFilePermission(file) {
	frappe.call({
		method: 'edu_quality.edu_quality.doctype.ptm_scheduler.ptm_scheduler.check_file_permission',
		args: { 'file_url': file },
		callback: function (response) {
			if (response.message.status === 'success') {
				importCSVData(file);
			} else {
				frappe.msgprint(__('Only public files are allowed for upload.'));

			}
		}
	});
}

function importCSVData(file) {
	let filters = frappe.query_report.get_filter_values(true);
	frappe.call({
		method: 'edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.import_mark_entry_csv',
		args: { 'url': file, filters: filters },
		callback: function (response) {
			if (response.message.status === 'success') {
				// Display success message with green indicator
				frappe.msgprint('<div style="color: green;">Success: ' + response.message.message + '</div>');
			} else {
				// Display failure message with red indicator
				frappe.msgprint('<div style="color: red;">Import failed: <br>' + response.message.message + '</div>');
			}
		},
		error: function (xhr, textStatus, error) {
			// Handle error in making the AJAX call
			frappe.msgprint('<div style="color: red;">Error occurred while importing data: <br>' + error + '</div>');
		}
	});
}

function addImportExportTemplate(report) {
	report.page.add_custom_menu_item(report.page.menu_btn_group, "Export Template", () => {
		let filters = report.get_filter_values(true);
		let reportName = "Marks Entry Tool"
		open_url_post(frappe.request.url, {
			cmd: "edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.export_custom_csv",
			report_name: reportName,
			filters: filters
		})



	})
	report.page.add_custom_menu_item(report.page.menu_btn_group, "Import Template", () => {
		var dialog = new frappe.ui.Dialog({
			title: __('Upload CSV File'),
			fields: [
				{
					fieldname: 'file',
					label: __('CSV File'),
					fieldtype: 'Attach',
					reqd: 1
				}
			],
			primary_action_label: __('Import'),
			primary_action: function () {
				var file = dialog.get_value('file');
				if (file) {
					let res = checkFilePermission(file);
					if (res != false) {
						dialog.hide();
					}

				} else {
					frappe.msgprint(__('Please select a file.'));
				}
			}
		});
		dialog.show();
	})
}

function onload(report) {
	initializeKeyListener();
	var queryParams = frappe.utils.get_query_params();
	addImportExportTemplate(report)
	frappe.require(["/assets/edu_quality/css/mark-entry-tool.css"]);
	report.page.parent.classList.add("mark-entry-tool-report");
	addNote()
	report.page.add_inner_button(__('Cancel Result'), () => {
		let indexes = frappe.query_report.datatable.rowmanager.getCheckedRows();
		let selected_rows = indexes.map(i => frappe.query_report.data[i]);

		if (selected_rows.length == 0) {
			frappe.msgprint(__("Select a row before cancelling a result"))
			return
		}
		const ref_nos = selected_rows.map((selected_row) => selected_row.ref_no)
		let message = `
			<div>
				
				<p>Are you sure you want to cancel result for selected row ? this will cancel all the results in a row irrespective of subject</p>
			</div>`;


		frappe.confirm(__(message), async () => {
			await cancelResult(ref_nos)
		})
	})
	report.page.add_inner_button(__('Process Result'), () => {
		const message = `
        <div>    
            <p>Are you sure you want to Leave this page and go to exam processing?</p>
        </div>`;

		frappe.confirm(__(message), async () => {
			goToProcessing()

		});


	});
	report.page.add_inner_button(__('Save Marks Entry'), () => {
		const message = `
        <div>    
            <p>Are you sure you want to Save Marks Entered?</p>
        </div>`;

		frappe.confirm(__(message), async () => {
			await saveCall()

		});
	});

	report.page.add_inner_button(__('Send Marks'), () => {
		let assessment_group = report.get_filter_value("assessment_group");
		let division = report.get_filter_value("division");
		if (!assessment_group) {
			frappe.msgprint({
				title: __('Assessment Group Required'),
				message: __('Please select Assessment Group'),
				indicator: 'orange',
				primary_action: {
					label: 'Okay',
					action: () => {
						cur_dialog.hide();
					}
				}
			})
			return
		}
		let dialog = new frappe.ui.Dialog({
			title: __("Send Marks"),
			fields: [
				{
					fieldname: "assessment_group",
					label: __("Assessment Group"),
					fieldtype: "Link",
					options: "Assessment Group",
					read_only: 1,
				},
				{
					fieldname: "all_division",
					label: __("All Division"),
					fieldtype: "Check",
				},
				{
					fieldname: "division",
					label: __("Division"),
					fieldtype: "Link",
					options: "Student Group",
					depends_on: "eval: !doc.all_division",
					read_only: 1,
				}
			],
			primary_action: async function () {
				dialog.hide();
				let print_format = await frappe.db.get_value("Assessment Group", assessment_group, "result_print_format");
				if (!print_format.message.result_print_format) {
					frappe.msgprint({
						title: __('Result Print Format Required'),
						message: __('Result Print Format must be present in Assessment Group'),
						indicator: 'orange',
						primary_action: {
							label: 'Okay',
							action: () => {
								cur_dialog.hide();
							}
						}
					})
				} else {
					frappe.confirm(__("Are you sure you want to send marks?"),
						() => {
							let values = dialog.get_values();
							if (!values) return;
							sendMarks(values.assessment_group, values.division)
						},
						() => {
							frappe.show_alert({
								message: __('Marks Sending Cancelled'),
								indicator: 'orange'
							});
						}
					);
				}
			},
			primary_action_label: __("Send")
		});
		dialog.show();
		dialog.set_values({
			assessment_group: report.get_filter_value("assessment_group"),
			all_division: division.length == 0,
			division: report.get_filter_value("division")
		});
	});

	if (frappe.query_report.get_filter_value("mode")) {
		report.page.add_inner_button(__('Switch to Marks Entry'), () => {

			let message = `
				<div>
					
					<p>Are you sure you want to go to normal marks entry</p>
				</div>`;

			frappe.confirm(__(message), async () => {
				switchToNormal()
			})


		})
	}

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
	const legends = [
		{ label: "Absent", "class": "absent-input" },
		{ label: "Online Assessment", "class": "assess-input" },
		{ label: "Submitted/Processed", "class": "submitted-input" },

	]
	const legendContainer = document.createElement('div')
	legendContainer.classList.add("legend-container")

	const generatedLegends = legends.map((el) => {
		return `<div class="legend"><div class="${el.class}"></div><div>${el.label}</div></div>`
	}).join('')

	legendContainer.innerHTML = generatedLegends

	noteContainerDiv.classList.add("note-container", "blue", "form-message", "my-0")
	noteContainerDiv.innerHTML = `
	
	<ul style="padding-left:16px;">
	<li>Non Submitted Exam Config Subjects inside an Exam Configuration and their subject components won't show up for marking</li>
	<li>Use - for marking student as absent</li>
	<li>Empty Columns will be marked as absent automatically, on first save</li>
	<li>Yellow Columns will be marked as absent automatically, on first save</li>
	</ul>
	`
	noteContainerDiv.appendChild(legendContainer)
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
		}, {
			"fieldname": "mode",
			"label": __("Online Mode"),
			"fieldtype": "Check",
			"hidden": true
		},
		{
			"fieldname": "remarks",
			"label": __("Remarks"),
			"fieldtype": "Check",
		},
		{
			"fieldname": "ref_no",
			"label": __("Online Mode"),
			"fieldtype": "Link",
			"options": "Student",
		}
	],
	"formatter": formatter,
	"onload": onload,

	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true
		});
	}
};