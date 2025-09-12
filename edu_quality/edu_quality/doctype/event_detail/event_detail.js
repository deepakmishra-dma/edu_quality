// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Event Detail", {
    add_allowed_students: (frm) => { showAddStudent(frm); },
    add_to_participating: (frm) => { addToParticipating(frm); },

    refresh(frm) {
        frm.add_custom_button('Send Registration Link', () => {
            sendRegistrationLink(frm);
        });
    },

});


function showAddStudent(frm) {
    let d = new frappe.ui.Dialog({
        title: 'Add Students',
        fields: [
            {
                label: 'Enter Reference Numbers Separated by Comma',
                fieldname: 'reference_number',
                fieldtype: 'Small Text',
            },
            {
                label: 'Student Status',
                fieldname: 'student_status',
                fieldtype: 'Select',
                options: 'New student\nCurrent student\nCancelled\nNot attending\nDefaulter\nAlumni',
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
            school: frm.doc.school,
            student_status: values.student_status,
            reference_number: values.reference_number,
        }
    })

    let allowed_students = frm.get_field("allowed_students");
    if (students.message.length == 0) {
        frappe.msgprint("No Student Found");
        return;
    }
    students.message.forEach(student => {
        let new_row = allowed_students.grid.add_new_row();
        new_row.student = student.name;
        new_row.student_name = student.student_name;
    });
    frm.refresh_field("allowed_students");
    frm.refresh();
}

function sendRegistrationLink(frm) {
    frappe.call({
        doc: frm.doc,
        method: 'send_registration_link',
        args: {
            data: frm.doc.allowed_students
        },
        callback: function (response) {
            if (response.message) {
                frappe.msgprint("Registration Link Sent Successfully");
            }
        }
    });
}


function addToParticipating(frm) {
    let allowed_students = frm.doc.allowed_students;
    let participating_students = frm.doc.participating_students;

    allowed_students.forEach(student => {
        if (student.__checked) {
            let already_participating = participating_students.some(participant => participant.student === student.student);
            
            if (!already_participating) {
                let new_row = frm.add_child("participating_students");
                new_row.student = student.student;
                new_row.student_name = student.student_name;
            }
        }
    });

    frm.refresh_field("participating_students");
    frm.refresh();
}
