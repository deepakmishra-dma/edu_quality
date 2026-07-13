frappe.ui.form.on("Assessment Group", {
  is_group: (frm) => {
    if (frm.doc.is_group == 0) frm.set_field("custom_is_composite", 0);
  },
  refresh: (frm) => {
    cur_frm.fields_dict["custom_composite_exams"].grid.get_field(
      "assesment_group"
    ).get_query = function (doc, cdt, dn) {
      let d = locals[cdt][dn];
      return {
        filters: {
          is_group: 0,
          custom_is_composite: 0,
        },
      };
    };
  },
});

frappe.ui.form.on("Composite Exam", {
  assesment_group: function (frm, cdt, cdn) {
    checkDuplicates(frm, cdt, cdn);
  },
});

function checkDuplicates(frm, cdt, cdn) {
  var d = locals[cdt][cdn];
  if (!d.assesment_group) {
    return;
  }
  frm.doc.custom_composite_exams.forEach(function (row, i) {
    if (row.assesment_group === d.assesment_group && row.name != d.name) {
      frappe.msgprint(
        `Assessment Group ${row.assesment_group} already added in composite exam`
      );
      frappe.model.remove_from_locals(cdt, cdn);
      frm.refresh_field("assessment_criteria");
      return false;
    }
  });
}
