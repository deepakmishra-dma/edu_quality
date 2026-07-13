function queryTextbook(frm) {
  frm.set_query("custom_textbook", function () {
    return {
      filters: {
        subject: frm.doc.custom_subject,
        class: frm.doc.custom_class,
      },
    };
  });
}
frappe.ui.form.on("Topic", {
  custom_class: queryTextbook,
  custom_subject: queryTextbook,
  refresh: function (frm) {
    queryTextbook(frm);
  },
});
