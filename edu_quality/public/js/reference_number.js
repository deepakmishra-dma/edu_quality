frappe.ui.form.on("Reference Number Settings", {
  refresh: function (frm) {
    frm.add_custom_button("Generate for Next Year", function () {
      frappe.call({
        method:
          "edu_quality.edu_quality.doctype.reference_number_settings.reference_number_settings.generate_next",
        args: {
          doc: cur_frm.doc.name,
        },
        callback: function (r) {
          if (!r.exc) {
            pass;
          }
        },
      });
    });
  },
});
