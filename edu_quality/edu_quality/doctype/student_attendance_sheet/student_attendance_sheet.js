const updatedAttendance = {};
let saveButtonAdded = false;
let globalFrm = null;
let showBtnEnable = false;

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

      const tableContainer = document.createElement("div");
      tableContainer.id = "report-table-container";

      const showBtn = document.createElement("button");
      showBtn.className = "btn btn-default btn-sm my-4";
      showBtn.innerText = "Show";
      showBtn.addEventListener("click", async () => {
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
      });
      showBtn.style.backgroundColor = "#3B84C3";
      showBtn.style.color = "#fff";
      showBtn.style.alignSelf = "center";
      attendanceContainer.appendChild(showBtn);
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
  },
});

function addSaveButton() {
  if (saveButtonAdded) return;
  saveButtonAdded = true;
  globalFrm.page.add_inner_button(__("Submit"), saveAttendance);
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

  const tableData = await frappe.call({
    method:
      "edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet.get_data",
    args: {
      month_name: frm.doc.month,
      academic_year: frm.doc.year,
      program: frm.doc.class,
      division: division,
    },
  });

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

  container.appendChild(
    createTable(headers, studentsList.message, days.message, tableData.message)
  );
  if (!frm.doc.division && division) {
    const pageBreakDiv = document.createElement("div");
    pageBreakDiv.style = "page-break-before: always;";
    container.appendChild(pageBreakDiv);
  }
}

function createTable(headers, studentsList, days, data) {
  const table = document.createElement("table");
  table.className = "table table-bordered table-responsive";
  const thead = document.createElement("thead");
  thead.style.backgroundColor = "#3B84C3";
  thead.style.color = "#fff";
  const tbody = document.createElement("tbody");
  const headerRow = document.createElement("tr");

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
    });
  }
  tbody.addEventListener("change", changeHandler);
  thead.appendChild(headerRow);
  table.appendChild(thead);

  table.appendChild(tbody);
  return table;
}

function createRow(ref_no, first_name, last_name, roll_no, days, data) {
  let rowHtml = `<tr>
  <td>${ref_no}</td>
    <td colspan="2" style='text-wrap:nowrap;'>${first_name}</td>
    <td colspan="2" style='text-wrap:nowrap;'>${last_name}</td>
    <td>${roll_no}</td>`;

  // Generate empty <td> elements for each day
  for (let i = 0; i < days.length; i++) {
    rowHtml += `<td  class='empty-td' style={width: 100px;}><input type='text' class='empty-input' data-day=${
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
