frappe.ui.form.on("Fee Schedule", {
  refresh: function (frm) {},

  fee_structure: function (frm) {
    student_group(frm);
  },
});

function student_group(frm) {
  // Fetch the selected program
  frm.clear_table("student_groups");
  var selectedProgram = frm.doc.program;
  // Clear existing child table entries
  // Fetch student groups based on the selected program using client API
  frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Fee Structure",
      filters: {
        name: frm.doc.fee_structure,
      },
      fields: ["program"], // Assuming 'name' is the student group identifier
    },
    callback: function (response) {
      if (response.message) {
        frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Student Group",
            filters: {
              program: response.message[0].program,
              academic_year: frm.doc.academic_year,
            },
            fields: ["name"], // Assuming 'name' is the student group identifier
          },
          callback: function (response) {
            if (response.message) {
              // Populate child table with fetched student groups
              response.message.forEach(function (studentGroup) {
                var childRow = frm.add_child("student_groups");
                childRow.student_group = studentGroup.name;
              });
              cur_frm.refresh_field("student_groups");
            }
          },
        });
      }
    },
  });
}
