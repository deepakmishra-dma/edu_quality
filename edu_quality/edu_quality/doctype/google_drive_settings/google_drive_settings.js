// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Google Drive Settings", {
  // refresh: function(frm) {

  // }
  authorize: function (frm) {
    frappe.call({
      method:
        "edu_quality.edu_quality.doctype.google_drive_settings.google_drive_settings.authorize_access",
      args: {
        reauthorize: frm.doc.auth_code ? 1 : 0,
      },
      callback: function (r) {
        if (!r.exc) {
          frm.save();
          window.open(r.message.url);
        }
      },
    });
  },
});
