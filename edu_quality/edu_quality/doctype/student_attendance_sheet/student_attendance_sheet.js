let updatedAttendance = {};
let saveButtonAdded = false;
let globalFrm = null;
let showBtnEnable = false;
let tables = [];
let holidays = [];
let showInfoTable = false;

frappe.ui.form.on("Student Attendance Sheet", {
  onload(frm) {
    globalFrm = frm;
    frm.set_query("year", function () {
      // Get the current year
      let currentYear = new Date().getFullYear().toString();

      return {
        filters: [
          ["Academic Year", "academic_year_name", "like", `${currentYear}%`],
        ],
      };
    });
  },
  refresh(frm) {
    frm.disable_save();

    var isUpdated = frm.doc.__unsaved;
    if (isUpdated) {
      frm.add_custom_button(__("teste"), function () {
        saveAttendance();
      });
    }
    const monthName = getCurrentMonthName();
    if (monthName) frm.set_value("month", monthName);
    globalFrm.page.add_inner_button(__("Print"), async () => {
      let pdfUrl;
      try {
        const headers = new Headers();
        headers.append("X-Frappe-CSRF-Token", frappe.csrf_token);
        headers.append("Content-Type", "application/json");
        const payload = { tables: tables, type: "POST" };
        const generated = await fetch(
          `/api/method/edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.generate`,
          {
            method: "POST",

            headers: headers,
            body: JSON.stringify(payload),
          }
        );
        const file = await generated.blob();
        pdfUrl = URL.createObjectURL(file);

        window.open(pdfUrl, "_blank");
      } catch (e) {
        console.error(e, "error message from pdf");
      } finally {
        if (pdfUrl) {
          URL.revokeObjectURL(pdfUrl);
        }
      }
    });
  },
  year: function (frm) {
    if (!showBtnEnable) frm.trigger("class");
  },
  division: function (frm) {
    if (!showBtnEnable) frm.trigger("class");
  },
  class: function (frm) {
    if (frm.doc.month && frm.doc.year && frm.doc.class && !showBtnEnable) {
      showBtnEnable = true;
      const attendanceContainer = document.querySelector(
        "#attendance_table_container"
      );
      attendanceContainer.className = "d-flex flex-column";

      const infoTableContainer = document.createElement("div");
      infoTableContainer.id = "info-table-container";

      const tableContainer = document.createElement("div");
      tableContainer.id = "report-table-container";
      const showBtn = document.createElement("button");
      showBtn.className = "btn btn-default btn-sm my-4";
      showBtn.innerText = "Show";
      showBtn.addEventListener("click", async () => {
        tables = [];
        updatedAttendance = {};
        if (frm.doc.division) {
          setupDataTable(frm, frm.doc.division);
        } else {
          const pageBreakDiv = document.createElement("div");
          pageBreakDiv.style = "page-break-before: always;";
          const divisions = await frappe.call({
            method:
              "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.get_divisions",
            args: {
              academic_year: frm.doc.year,
              program: frm.doc.class,
            },
          });

          divisions.message.forEach((division, index) => {
            setupDataTable(frm, division.name);
          });
        }
        if (!showInfoTable) {
          infoTableContainer.appendChild(infoTable());
          displayNotes(infoTableContainer);
          showInfoTable = true;
        }
      });
      showBtn.style.backgroundColor = "#3B84C3";
      showBtn.style.color = "#fff";
      showBtn.style.alignSelf = "center";
      attendanceContainer.appendChild(showBtn);
      attendanceContainer.appendChild(infoTableContainer);
      attendanceContainer.appendChild(tableContainer);
    }
    frm.set_query("division", function () {
      let filters = [["Student Group", "program", "=", frm.doc.class]];
      if (frm.doc.year) {
        filters.push(["Student Group", "academic_year", "=", frm.doc.year]);
      }
      return {
        filters: filters,
      };
    });
    frm.set_value("division", "");
  },
});

function addSaveButton() {
  if (saveButtonAdded) return;
  saveButtonAdded = true;
  globalFrm.page.remove_inner_button(__("Submit"));
  globalFrm.page.add_inner_button(__("Save"), saveAttendance);
}
function changeHandler(e) {
  const dataset = e.target.dataset;

  if (dataset.day && dataset.ref) {
    if (updatedAttendance.hasOwnProperty(dataset.ref)) {
      const existingDayIndex = updatedAttendance[dataset.ref].findIndex(
        (item) => Object.keys(item)[0] === dataset.day
      );
      if (existingDayIndex !== -1) {
        updatedAttendance[dataset.ref][existingDayIndex][dataset.day] =
          e.target.value;
      } else {
        updatedAttendance[dataset.ref].push({ [dataset.day]: e.target.value });
      }
    } else {
      updatedAttendance[dataset.ref] = [{ [dataset.day]: e.target.value }];
    }
  }
  addSaveButton();
}
async function setupDataTable(frm, division) {
  const container = document.getElementById("report-table-container");
  container.innerHTML = "";

  const attendanceData = await frappe.call({
    method:
      "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.get_data",
    args: {
      month_name: frm.doc.month,
      academic_year: frm.doc.year,
      program: frm.doc.class,
      division: division,
    },
  });

  if (attendanceData.message.holidays) {
    holidays = attendanceData.message.holidays;
  }

  const studentsList = await frappe.call({
    method:
      "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.get_students",
    args: {
      program: frm.doc.class,
      division: division,
    },
  });

  const days = await frappe.call({
    method:
      "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.get_days_in_month",
    args: {
      month_name: frm.doc.month,
      academic_year: frm.doc.year,
    },
  });

  const headers = [
    { textContent: "Ref No" },
    { textContent: "First Name", colSpan: 2 },
    { textContent: "Last Name", colSpan: 2 },
    { textContent: "Roll No" },
    ...days.message,
  ];

  if (studentsList.message.length > 0) {
    container.appendChild(
      createTable(
        headers,
        studentsList.message,
        days.message,
        attendanceData.message.table_data,
        division
      )
    );
  } else if (studentsList.message.length === 0 && !frm.doc.division) return;
  else {
    container.innerHTML = "<p>No students found for selected division</p>";
  }

  if (!frm.doc.division && division) {
    const pageBreakDiv = document.createElement("div");
    pageBreakDiv.style = "page-break-before: always;";
    container.appendChild(pageBreakDiv);
  }
}

function createTable(headers, studentsList, days, data, division) {
  const table = document.createElement("table");
  table.className = "table table-bordered table-responsive";
  const thead = document.createElement("thead");
  thead.style.backgroundColor = "#3B84C3";
  thead.style.color = "#fff";
  const tbody = document.createElement("tbody");
  const headerRow = document.createElement("tr");
  const curTableData = { columns: [], rows: [] };

  headers.forEach((header) => {
    const headerCell = document.createElement("th");
    headerCell.textContent = header.textContent;
    if (header.className) {
      headerCell.className = header.className;
    }
    if (header.colSpan) {
      headerCell.colSpan = header.colSpan;
    }
    headerRow.appendChild(headerCell);

    if (!holidays.includes(Number(header.textContent))) {
      curTableData.columns.push(header);
    }
  });

  if (studentsList.length != 0) {
    studentsList.forEach((row, index) => {
      const row_html = createRow(
        row.reference_number,
        row.first_name,
        row.last_name,
        index + 1,
        days,
        data
      );
      tbody.innerHTML += row_html;
      curTableData.rows.push(row_html);
    });
  }
  tbody.addEventListener("change", changeHandler);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  table.appendChild(tbody);
  division;
  const tableObj = {
    table: curTableData,
    class: globalFrm.doc.class,
    division: division,
    month: globalFrm.doc.month,
    year: globalFrm.doc.year,
  };
  tables.push(tableObj);
  return table;
}

function createRow(ref_no, first_name, last_name, roll_no, days, data) {
  let rowHtml = `<tr>
  <td style='white-space: nowrap; min-width: fit-content !important;'>${ref_no}</td>
    <td colspan="2" style='text-wrap:nowrap;min-width: fit-content !important;'>${first_name.toUpperCase()}</td>
    <td colspan="2" style='text-wrap:nowrap;min-width: fit-content !important;'>${last_name.toUpperCase()}</td>
    <td style='white-space: nowrap; min-width: fit-content !important;'>${roll_no}</td>`;

  // Generate empty <td> elements for each day
  for (let i = 0; i < days.length; i++) {
    rowHtml += `<td  class='empty-td ${
      holidays.includes(i + 1) ? "holiday" : ""
    }' style='width: 42px; min-width: 42px;'><input type='text' class='empty-input' data-day=${
      i + 1
    } data-ref=${ref_no} style='width: 25px;' value=${
      data[ref_no][i][i + 1]
    } ></input></td>`;
  }

  rowHtml += `</tr>`;
  return rowHtml;
}

function saveAttendance() {
  frappe.call({
    method:
      "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.save_attendance",
    args: {
      month_name: globalFrm.doc.month,
      academic_year: globalFrm.doc.year,
      program: globalFrm.doc.class,
      division: globalFrm.doc.division,
      attendance_data: JSON.stringify(updatedAttendance),
    },
    callback: function (response) {
      if (response.message) {
        saveButtonAdded = false;
        globalFrm.page.remove_inner_button(__("Save"));
        showSubmitBtn(true);
      }
      frappe.show_alert({
        message: __(response.message),
        indicator: "green",
      });
    },
  });
}

function checkAttendance() {
  frappe.call({
    method:
      "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.check_attendance_entry",
    args: {
      month_name: globalFrm.doc.month,
      academic_year: globalFrm.doc.year,
      program: globalFrm.doc.class,
    },
    callback: function (response) {
      if (response.message) {
        frappe.confirm(
          __(
            "There is a Sick or Early Pickup or Late attendance entry. You are allowed to submit Absent or Present. If you continue, we'll mark early pick up and late as present and sick as absent. Do you want to continue?"
          ),
          function () {
            submitAttendance();
          }
        );
      }
    },
  });
}

function submitAttendance() {
  frappe.call({
    method:
      "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.submit_attendance",
    args: {
      month_name: globalFrm.doc.month,
      academic_year: globalFrm.doc.year,
      program: globalFrm.doc.class,
      division: globalFrm.doc.division,
    },
    callback: function (response) {
      if (response.message) {
        showSubmitBtn(false);
      }
      frappe.show_alert({
        message: __(response.message),
        indicator: "green",
      });
      frm.reload_doc();
    },
  });
}

function getCurrentMonthName() {
  const currentDate = new Date();
  return currentDate.toLocaleString("default", { month: "long" });
}

function showSubmitBtn(showSubmitBtn) {
  if (showSubmitBtn) {
    globalFrm.page.add_inner_button(__("Submit"), checkAttendance);
  } else {
    globalFrm.page.remove_inner_button(__("Submit"));
  }
}

function infoTable() {
  const table = document.createElement("table");
  table.className = "table table-bordered table-responsive";
  table.style.width = "fit-content";
  table.style.margin = "auto";
  table.style.textAlign = "center";
  const thead = document.createElement("thead");
  thead.style.backgroundColor = "#3B84C3";

  thead.style.color = "#fff";

  const columns = ["P", "A", "L", "E", "S"];
  const rowContent = [
    "Present",
    "Absent",
    "Late Pickup",
    "Early Pickup",
    "Sick",
  ];

  const headerRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column.trim();
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  const tbody = document.createElement("tbody");

  const contentRow = document.createElement("tr");
  rowContent.forEach((content) => {
    const td = document.createElement("td");
    td.textContent = content.trim();
    contentRow.appendChild(td);
  });
  tbody.appendChild(contentRow);

  table.appendChild(thead);
  table.appendChild(tbody);

  return table;
}

function displayNotes(container) {
  const combinedMessage = `
  <div >
  <strong>Note:</strong>
<ul style="font-size: smaller;">
  <li> Please enter only Absent. Present will be populated for the blank entries.</li>
  <li>You can't edit submitted entries.</li>
</ul>
</div>`;

  const noteContainer = document.createElement("div");
  noteContainer.className = "d-flex justify-content-center mt-2";
  noteContainer.innerHTML = combinedMessage;
  container.appendChild(noteContainer);
}
