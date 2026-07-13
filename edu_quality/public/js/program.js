frappe.ui.form.on("Program", {
  refresh: function (frm) {
    frm
      .add_custom_button(__("Shuffle Division"), function () {
        shuffleDivision(frm);
      })
      .addClass("btn-primary");
  },
});

async function shuffleDivision(frm) {
  let data = await getDivisionMessage(frm);

  var dialog = new frappe.ui.Dialog({
    title: "Shuffle Division",
    fields: [
      {
        fieldtype: "Button",
        label: "Export Student Details",
        fieldname: "export",
        click: function () {
          frappe.call({
            doc: frm.doc,
            method: "export_student_details",
            args: {
              program: frm.doc.name,
            },
            callback: function (response) {
              if (!response.message) {
                displayMessage(
                  "Error while exporting student details, Please click on 'Shuffle Division' and Try again."
                );
                return;
              }
              var a = document.createElement("a");
              var filecontent = atob(response.message.filecontent);
              var blob = new Blob([filecontent], { type: "application/csv" });
              var url = window.URL.createObjectURL(blob);
              a.href = url;
              a.download = response.message.filename;
              document.body.append(a);
              a.click();
              a.remove();
              window.URL.revokeObjectURL(url);
            },
          });
        },
      },
      {
        fieldtype: "HTML",
        label: "Details",
        fieldname: "details",
        options: data,
      },
    ],
    size: "large",
    primary_action_label: "Okay",
    primary_action: function () {
      frappe.call({
        doc: frm.doc,
        async: true,
        freeze: true,
        method: "shuffle_divisions",
        args: {
          program: frm.doc.name,
        },
        callback: function (r) {
          if (!r.message) {
            displayMessage(
              "Error while shuffling division data, Please click on 'Shuffle Division' and Try again."
            );
            return;
          }
          if (r.message) {
            frappe.show_alert({
              message: __(r.message),
              indicator: "green",
            });
          }
        },
      });
      dialog.hide();
    },
  });

  dialog.show();
}

async function getDivisionMessage(frm) {
  const data = await frappe.call({
    doc: frm.doc,
    method: "get_possible_allocations",
    args: {
      program: frm.doc.name,
    },
  });

  if (!data.message) {
    return "Error while getting student details";
  }

  data.message = Object.keys(data.message)
    .sort()
    .reduce((obj, key) => {
      obj[key] = data.message[key];
      return obj;
    }, {});

  const html_content = Object.keys(data.message)
    .map((key) => {
      const details = data.message[key];
      let boysCount = details.filter(
        (detail) => detail.gender === "Male"
      ).length;
      let girlsCount = details.filter(
        (detail) => detail.gender === "Female"
      ).length;
      let blueHouseCount = details.filter(
        (detail) => detail.house === "Blue"
      ).length;
      let redHouseCount = details.filter(
        (detail) => detail.house === "Red"
      ).length;
      let greenHouseCount = details.filter(
        (detail) => detail.house === "Green"
      ).length;
      let yellowHouseCount = details.filter(
        (detail) => detail.house === "Yellow"
      ).length;
      return `
            <details>
                <summary>${key}</summary>
                <p>Total Students: ${details.length}</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr;">
                    <p>Boys: ${boysCount}</p>
                    <p>Girls: ${girlsCount}</p>
                    <p>Yellow: ${yellowHouseCount}</p>
                    <p>Green: ${greenHouseCount}</p>
                    <p>Red: ${redHouseCount}</p>
                    <p>Blue: ${blueHouseCount}</p>
                </div>
                <details>
                    <summary>Students</summary>
                    <div style="display: grid; grid-template-columns: 1fr 1fr;">
                        ${details
                          .map((student) => {
                            return `<p>${student.name}: ${student.first_name}-${student.house}</p>`;
                          })
                          .join("")}
                    </div>
                </details>
            </details>
        `;
    })
    .join("");

  return `<div style="display: grid; grid-template-columns: 1fr 1fr;">${html_content}</div>`;
}

function displayMessage(message) {
  frappe.msgprint({
    title: __("Error!"),
    message: __(message),
    primary_action: {
      label: __("OK"),
      action: function () {
        frappe.hide_msgprint();
      },
    },
  });
}
