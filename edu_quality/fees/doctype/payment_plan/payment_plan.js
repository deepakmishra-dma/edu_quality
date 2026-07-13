// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Plan", {
  refresh: function (frm) {
    if (frm.is_new()) {
      // To set Academic Year
      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "Academic Year",
          filters: [
            ["year_start_date", "<=", "18-08-2023"],
            ["year_end_date", ">=", "18-08-2023"],
          ],
        },
        callback: function (response) {
          var records = response.message;
          if (records) {
            frm.set_value("academic_year", records[0].name);
            frm.refresh_field("academic_year");
          }
        },
      });
    }
  },
  program: function (frm) {
    set_fee_structure(frm);
  },
  school: function (frm) {
    set_fee_structure(frm);
  },
});
// to set Fee Structure
function set_fee_structure(frm) {
  frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Fee Structure",
      filters: [
        ["program", "=", frm.doc.program],
        ["academic_year", "=", frm.doc.academic_year],
        ["school", "=", frm.doc.school],
      ],
    },
    callback: function (response) {
      var feeStructures = response.message;
      if (feeStructures) {
        frm.set_value("fee_structure", feeStructures[0].name);
        frm.refresh_field("fee_structure");
      }
    },
  });
}
