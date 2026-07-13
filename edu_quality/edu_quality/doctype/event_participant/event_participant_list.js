// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.listview_settings["Event Participant"] = {
  onload: function (listview) {
    listview.page.add_menu_item(__("Export Data"), function () {
      var dialog = new frappe.ui.Dialog({
        title: __("Export Participant Data"),
        fields: [
          {
            fieldname: "event_detail",
            label: __("Event Detail"),
            fieldtype: "Link",
            options: "Event Detail",
            reqd: 1,
          },
        ],
        primary_action_label: __("Export"),
        primary_action: function () {
          var event_detail = dialog.get_value("event_detail");
          if (event_detail) {
            exportParticipantData(event_detail);
            dialog.hide();
          } else {
            frappe.msgprint(__("Please select an event."));
          }
        },
      });
      dialog.show();
    });
  },
};

function titleCase(str) {
  return str
    .toLowerCase()
    .split(" ")
    .map(function (word) {
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}

function showParticipantDetails(frm) {
  if (!frm.is_new()) {
    const container = frm.$wrapper[0].querySelector("#participant_details");
    if (frm.doc.data) {
      let data = JSON.parse(frm.doc.data);
      const tableRows = Object.entries(data)
        .map(([key, value]) => {
          return `
                    <tr>
                    <td>${titleCase(key.replace("_", " "))}</td>
                    <td>${value}</td>
                    </tr>
                `;
        })
        .join("");

      container.innerHTML = `
                <h3>Participant Details</h3>
                <table class="table table-bordered">
                    <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Data</th>
                    </tr>
                    </thead>
                    <tbody>
                    ${tableRows}
                    </tbody>
                </table>
                `;
    }
  }
}

function exportParticipantData(event_detail) {
  frappe.call({
    method:
      "edu_quality.edu_quality.doctype.event_participant.event_participant.export_participant_data",
    args: {
      event_detail: event_detail,
    },
    callback: function (r) {
      if (r.message) {
        console.log(r.message);
        const csvData = convertJSONToCSV(r.message);
        downloadCSV(csvData, "participant_data.csv");
      }
    },
  });
}

function convertJSONToCSV(jsonData) {
  if (!jsonData || jsonData.length === 0) {
    return "";
  }
  const keys = Object.keys(jsonData[0]);
  const csvRows = [];
  jsonData.map((data) => {
    // Add the headers
    csvRows.push(keys.join(","));

    // Add the data
    const values = keys.map((key) =>
      JSON.stringify(data[key], (key, value) => (value === null ? "" : value))
    );
    csvRows.push(values.join(","));
  });

  return csvRows.join("\n");
}

function downloadCSV(csvData, filename) {
  const blob = new Blob([csvData], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.setAttribute("hidden", "");
  a.setAttribute("href", url);
  a.setAttribute("download", filename);
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
