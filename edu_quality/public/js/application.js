frappe.ui.form.on("Student Applicant", {
  onload: function (frm) {
    handleBatchVisibility(frm);
    $(".primary-action").prop("hidden", true);
  },

  refresh: function (frm) {
    if (!frm.is_new() && frm.doc.application_status !== "Admitted") {
      frm
        .add_custom_button(__("Send Web Form Link"), function () {
          frappe.confirm(
            "Are you sure you want to send Web Form Link?",
            () => {
              frappe.call({
                method:
                  "edu_quality.edu_quality.server_scripts.student_applicant.send_web_form_link",
                args: {
                  student_applicant: frm.doc.name,
                },
                callback: function (r) {
                  frappe.show_alert({
                    message: __("Web Form Link Sent..."),
                    indicator: "green",
                  });
                },
              });
            },
            () => {}
          );
        })
        .addClass("btn-primary");
    }

    frm.remove_custom_button("Approve", "Actions");
    frm.remove_custom_button("Enroll");
    if (!frm.is_new() && frm.doc.application_status === "Applied") {
      frm.set_value("application_status", "Approved");
      frm.save_or_update();
    } else if (frm.doc.application_status === "Approved") {
      frm
        .add_custom_button(__("Enroll"), function () {
          if (frm.doc.__unsaved) {
            frm.save_or_update();
          }
          frappe.confirm(
            "Have you checked all the data filled in by the parent in the admission form?",
            () => {
              if (checkFields(frm)) {
                frappe.show_alert({
                  message: __("Enrolling Student..."),
                  indicator: "green",
                });
                frm.events.enroll(frm);
              }
            },
            () => {
              frappe.show_alert({
                message: __("Student Enrollment Cancelled..."),
                indicator: "orange",
              });
            }
          );
        })
        .addClass("btn-primary");
    }
  },

  enroll: function (frm) {
    frappe.realtime.on("enroll_student_progress", function (data) {
      if (data.progress) {
        frappe.hide_msgprint(true);
        frappe.show_progress(
          __("Enrolling student"),
          data.progress[0],
          data.progress[1]
        );
      }
    });
    frappe.call({
      method: "edu_quality.public.py.application.enroll_student",
      args: {
        source_name: frm.docname,
      },
      callback: function (r) {
        if (r.message) {
          window.location.href = r.message;
        }
      },
    });
  },
  batch: function (frm) {
    frm.save_or_update();
  },
});

async function handleBatchVisibility(frm) {
  let student = await frappe.db.get_value(
    "Student",
    { student_applicant: frm.doc.name },
    "name"
  );
  if (student?.message?.name) {
    let pe = await frappe.db.get_value(
      "Program Enrollment",
      { student: student.message.name },
      "name"
    );
    frm.set_df_property("batch", "read_only", pe?.message?.name ? 1 : 0);
  }
}

function checkFields(frm) {
  const fields = ["school", "program", "academic_year", "batch"];
  const missingFields = fields.filter((field) => !frm.doc[field]);

  if (missingFields.length === 0) {
    return true;
  } else {
    frappe.msgprint({
      title: __("Missing Fields"),
      indicator: "red",
      message:
        __("Please fill the required fields") + ": " + missingFields.join(", "),
      primary_action: {
        label: "Close",
        action: function () {
          frappe.hide_msgprint();
        },
      },
    });
  }
}
