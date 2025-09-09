// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Event Details", {
    add_students: (frm) => { showAddStudent(frm); },

    refresh(frm) {

    },

});


function showAddStudent(frm) {
    let d = new frappe.ui.Dialog({
        title: 'Add Students',
        fields: [
            {
                label: 'By Class',
                fieldname: 'by_class',
                fieldtype: 'Check',
                default: 0,
                onchange: function () {
                    if (d.get_value('by_class')) {
                        d.set_df_property('program', 'hidden', 0);
                        d.set_df_property('division', 'hidden', 1);
                        d.set_df_property('reference_number', 'hidden', 1);
                        d.set_value('by_division', 0);
                        d.set_value('by_reference_number', 0);
                        d.refresh();
                    } else {
                        d.set_df_property('program', 'hidden', 1);
                    }
                }
            },
            {
                fieldtype: "Column Break",
            },
            {
                label: 'By Division',
                fieldname: 'by_division',
                fieldtype: 'Check',
                default: 0,
                onchange: function () {
                    if (d.get_value('by_division')) {
                        d.set_df_property('division', 'hidden', 0);
                        d.set_df_property('program', 'hidden', 1);
                        d.set_df_property('reference_number', 'hidden', 1);
                        d.set_value('by_class', 0);
                        d.set_value('by_reference_number', 0);
                        d.refresh();
                    } else {
                        d.set_df_property('division', 'hidden', 1);
                    }
                }
            },
            {
                fieldtype: "Column Break",
            },
            {
                label: 'By Reference Number',
                fieldname: 'by_reference_number',
                fieldtype: 'Check',
                default: 0,
                onchange: function () {
                    if (d.get_value('by_reference_number')) {
                        d.set_df_property('reference_number', 'hidden', 0);
                        d.set_df_property('division', 'hidden', 1);
                        d.set_df_property('program', 'hidden', 1);
                        d.set_value('by_class', 0);
                        d.set_value('by_division', 0);
                        d.refresh();
                    } else {
                        d.set_df_property('reference_number', 'hidden', 1);
                    }
                }
            },
            {
                fieldtype: "Section Break",
            },
            {
                label: 'Enter Reference Numbers Separated by Comma',
                fieldname: 'reference_number',
                fieldtype: 'Small Text',
                hidden: 1,
            },
            {
                label: 'Class',
                fieldname: 'program',
                fieldtype: 'Link',
                options: 'Program',
                hidden: 1,
            },
            {
                label: 'Division',
                fieldname: 'division',
                fieldtype: 'Link',
                options: 'Student Group',
                hidden: 1,
            }
        ],
        size: 'large',
        primary_action_label: 'Submit',
        primary_action: async function (values) {
            AddStudent(values, frm);
            d.hide();
        }
    });

    d.show();
}

async function AddStudent(values, frm) {
    let students = await frappe.call({
        doc: frm.doc,
        method: 'get_students',
        args: {
            program: values.program,
            division: values.division,
            reference_number: values.reference_number,
            school: frm.doc.school
        }
    })

    let allowed_students = frm.get_field("allowed_students");
    students.message.forEach(student => {
        let new_row = allowed_students.grid.add_new_row();
        new_row.student = student.name;
        new_row.student_name = student.student_name;
    });
    frm.refresh_field("allowed_students");
    frm.refresh();
}
