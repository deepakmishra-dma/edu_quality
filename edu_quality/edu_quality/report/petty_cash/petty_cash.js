// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Petty Cash"] = {
  filters: [
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
    },
    {
      fieldname: "school",
      label: __("School"),
      fieldtype: "Link",
      options: "School",
      get_query: function (txt) {
        const company = frappe.query_report.get_filter_value("company");
        return { filters: { institution: company } };
      },
    },
    {
      fieldname: "type",
      label: __("Type"),
      fieldtype: "Select",
      options: ["", "Payment", "Cash Withdrawal"],
    },
    {
      fieldname: "start_date",
      label: __("Start Date"),
      fieldtype: "Date",
    },
    {
      fieldname: "end_date",
      label: __("End Date"),
      fieldtype: "Date",
    },
    {
      fieldname: "show_only_draft",
      label: __("Show Only Draft"),
      fieldtype: "Check",
    },
  ],

  get_datatable_options(options) {
    return Object.assign(options, {
      checkboxColumn: true,
    });
  },

  onload: function (report) {
    if (hasRole("Accounts Manager")) {
      report.page.add_inner_button(__("Approve"), function () {
        handleApproval(report, "approve");
      });

      report.page.add_inner_button(__("Reject"), function () {
        handleApproval(report, "reject");
      });
    }
  },
};
// Define the custom hasRole function
function hasRole(role) {
  return frappe.user_roles && frappe.user_roles.includes(role);
}

function handleApproval(report, action) {
  const indexes = report.datatable.rowmanager.getCheckedRows();
  let selected_rows = indexes.map((i) => frappe.query_report.data[i]);

  if (selected_rows.length === 0) {
    frappe.msgprint(__("Please select rows to " + action));
    return;
  }

  const journal_entries = selected_rows
    .map((row) => row.voucher_no)
    .filter((voucher_no) => voucher_no !== "" && voucher_no !== null);

  if (journal_entries.length === 0) {
    frappe.msgprint(__("Please select rows with Voucher No"));
    return;
  }

  frappe.confirm(
    __("Are you sure you want to " + action + " the selected rows?"),
    function () {
      frappe.call({
        method:
          "edu_quality.edu_quality.report.petty_cash.petty_cash.handle_approval",
        args: { data: journal_entries, [action]: true },
        callback: function (r) {
          if (r.message) {
            let action_msg = action.charAt(0).toUpperCase() + action.slice(1);
            if (action === "reject") {
              action_msg += "ed";
            } else {
              action_msg += "d";
            }
            frappe.show_alert({
              message: __(action_msg),
              indicator: "green",
            });
            report.refresh();
          } else {
            frappe.show_alert({
              message: __("Failed to " + action),
              indicator: "red",
            });
          }
        },
      });
    }
  );
}
