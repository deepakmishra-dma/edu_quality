// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Event Detail", {
  add_allowed_students: (frm) => {
    showAddStudent(frm);
  },
  add_to_participating: (frm) => {
    addToParticipating(frm);
  },

  refresh(frm) {
    $("[data-fieldname='all_students'").attr(
      "title",
      "Select all students from the selected classes and school"
    );
    // sendRegistrationLink(frm);
    // Function to set query for student fields
    function set_student_query(fieldname) {
      frm.set_query("student", fieldname, function (doc, cdt, cdn) {
        const hasPrograms = doc.classes_applicable_to.some(
          (program) => program.class
        );
        const filters = {
          school: doc.school,
        };
        if (hasPrograms) {
          filters.program = [
            "in",
            doc.classes_applicable_to.map((program) => program.class),
          ];
        }
        return { filters };
      });
    }
    let child_tables = [
      "allowed_students",
      "participating_students",
      "non_participating_students",
      "winning_students",
    ];
    child_tables.forEach((child_table) => {
      set_student_query(child_table);
    });
  },

  // registration_type: (frm) => {
  //     sendRegistrationLink(frm);
  // }
});

function showAddStudent(frm) {
  let d = new frappe.ui.Dialog({
    title: "Add Students",
    fields: [
      {
        label: "Enter Reference Numbers Separated by Comma",
        fieldname: "reference_number",
        fieldtype: "Small Text",
      },
      {
        label: "Student Status",
        fieldname: "student_status",
        fieldtype: "Select",
        options:
          "New student\nCurrent student\nCancelled\nNot attending\nDefaulter\nAlumni",
      },
    ],
    size: "large",
    primary_action_label: "Submit",
    primary_action: async function (values) {
      AddStudent(values, frm);
      d.hide();
    },
  });

  d.show();
}

async function AddStudent(values, frm) {
  let students = await frappe.call({
    doc: frm.doc,
    method: "get_students",
    args: {
      school: frm.doc.school,
      student_status: values.student_status,
      reference_number: values.reference_number,
    },
  });

  let allowed_students = frm.get_field("allowed_students");
  if (students.message.length == 0) {
    frappe.msgprint("No Student Found");
    return;
  }
  students.message.forEach((student) => {
    let new_row = allowed_students.grid.add_new_row();
    new_row.student = student.name;
    new_row.student_name = student.student_name;
  });
  frm.refresh_field("allowed_students");
  frm.refresh();
}

function sendRegistrationLink(frm) {
  if (
    frm.doc.registration_type === "Pre-registered" ||
    frm.doc.registration_type === "Mix"
  ) {
    frm.add_custom_button("Send Registration Link", () => {
      frappe.confirm(
        "Are you sure you want to send registration link to all allowed students?",
        () => {
          frappe.call({
            doc: frm.doc,
            method: "send_registration_link",
            callback: function (response) {
              if (response.message) {
                frappe.show_alert({
                  message: __("Registration Link Sent Successfully"),
                  indicator: "green",
                });
              } else {
                frappe.show_alert({
                  message: __("Failed to send Registration Link"),
                  indicator: "red",
                });
              }
            },
          });
        },
        () => {
          frappe.show_alert({
            message: __("Action Cancelled"),
            indicator: "blue",
          });
        }
      );
    });
  } else {
    frm.remove_custom_button("Send Registration Link");
  }
}

function addToParticipating(frm) {
  let participating_students = frm.doc.participating_students;

  function addStudents(allowed_students) {
    if (frm.doc.all_students) {
      frm.clear_table("participating_students");
      allowed_students.forEach((student) => {
        let new_row = frm.add_child("participating_students");
        new_row.student = student;
      });
    } else {
      allowed_students.forEach((student) => {
        if (student.__checked) {
          let already_participating = participating_students.some(
            (participant) => participant.student === student.student
          );

          if (!already_participating) {
            let new_row = frm.add_child("participating_students");
            new_row.student = student.student;
            new_row.student_name = student.student_name;
          }
        }
      });
    }
    frm.refresh_field("participating_students");
    frm.save();
    frappe.show_alert({
      message: __("Students Added Successfully"),
      indicator: "green",
    });
  }
  let message = frm.doc.student_status
    ? `Student with status <b>${frm.doc.student_status}</b> will be added to participating students. Do you want to continue?`
    : `Do you want to add students to participating students?`;
  frappe.confirm(
    message,
    () => {
      if (frm.doc.all_students) {
        frappe.call({
          doc: frm.doc,
          method: "get_allowed_students",
          callback: function (response) {
            if (response.message) {
              addStudents(response.message);
            }
          },
        });
      } else {
        addStudents(frm.doc.allowed_students);
      }
    },
    () => {
      frappe.show_alert({
        message: __("Action Cancelled"),
        indicator: "blue",
      });
    }
  );
}
