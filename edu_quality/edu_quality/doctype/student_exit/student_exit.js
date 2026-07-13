// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Exit", {
  refresh(frm) {
    frm.add_custom_button(__("Update Details"), function () {
      frappe.call({
        doc: frm.doc,
        method: "update_details",
        callback: function (r) {
          frm.reload();
        },
      });
    });
  },
});
