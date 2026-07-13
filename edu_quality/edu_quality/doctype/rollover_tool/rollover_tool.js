// Copyright (c) 2016, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rollover Tool", {
  refresh: function (frm) {
    // frm.disable_save();
    frm.fields_dict.enroll_students.$input.addClass(" btn btn-primary");
    frappe.realtime.on("program_enrollment_tool", function (data) {
      frappe.hide_msgprint(true);
      frappe.show_progress(
        __("Enrolling students"),
        data.progress[0],
        data.progress[1]
      );
    });
    if (frm.doc.academic_year == "") {
      frappe.call({
        method: "get_current_academic_year",
        doc: frm.doc,
        callback: function (r) {
          if (r.message) {
            console.log(r.message);
            frm.set_value("academic_year", r.message);
          }
        },
      });
    }
  },

  get_students_from: function (frm) {
    if (frm.doc.get_students_from == "Student Applicant") {
      frm.dashboard.add_comment(
        __(
          'Only the Student Applicant with the status "Approved" will be selected in the table below.'
        )
      );
    }
  },

  get_students: function (frm) {
    frm.set_value("students", []);
    frappe.call({
      method: "get_students",
      doc: frm.doc,
      callback: function (r) {
        if (r.message) {
          frm.set_value("students", r.message);
        }
      },
    });
  },
  enroll_students: function (frm) {
    frappe.call({
      method: "enroll_students",
      doc: frm.doc,
      callback: function (r) {
        frm.set_value("students", []);
        frappe.hide_msgprint(true);
      },
    });
  },

  shift_reference_series: function (frm) {
    frappe.call({
      method: "shift_series",
      doc: frm.doc,
      callback: function (r) {
        frappe.msgprint("Shifted Reference Series for the classes!");
      },
    });
  },
  mark_as_rolled_over: function (frm) {
    frappe.call({
      method: "mark_rolled",
      doc: frm.doc,
      callback: function (r) {
        frappe.msgprint("Academic Year has been marked as Rollovered!");
      },
    });
  },
  see_possible_enrollments: function (frm) {
    let path =
      "/app/program-enrollment?docstatus=0&custom_school=" +
      encodeURIComponent(frm.doc.school);
    window.open(path, "_blank");
  },
});
