frappe.ui.form.on("Program Enrollment", {
    refresh: function (frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0) {
            frm.dashboard.clear_comment()
            frm.dashboard.add_comment(__('Please click Save and then click Create Fees'), 'blue');
            $('.primary-action').prop('hidden', true);
            frm.add_custom_button(__("Create Fees"), function () {
                frm.events.create_fees(frm)
            }).addClass("btn-primary");
            frm.add_custom_button(__("Save"), function () {
                frm.save()
            }).addClass("btn-primary");
        }
        frm.set_query("payment_plan", function () {
            return {
                filters: {
                    "program": frm.doc.program,
                    "academic_year": frm.doc.academic_year
                }
            };
        });
        frm.set_query("student_batch_name", function () {
            return {
                query: "edu_quality.edu_quality.server_scripts.utils.batch_filter",
                filters: { 'program': frm.doc.program, 'academic_year': frm.doc.academic_year }
            };
        });
    },

    create_fees: function (frm) {
        showPopup(frm);
    }
});


function showPopup(frm) {
    var dialog = new frappe.ui.Dialog({
        title: __('Fee Details'),
        fields: [
            {
                fieldtype: 'Read Only',
                label: __('Student Name'),
                fieldname: 'student_name',
                default: frm.doc.student_name
            },
            {
                fieldtype: 'Read Only',
                label: __('School'),
                fieldname: 'school',
                default: frm.doc.custom_school
            },
            {
                fieldtype: 'Read Only',
                label: __('Class'),
                fieldname: 'class_name',
                default: frm.doc.program
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Read Only',
                label: __('Academic Year'),
                fieldname: 'academic_year',
                default: frm.doc.academic_year
            },
            {
                fieldtype: 'Read Only',
                label: __('Batch'),
                fieldname: 'batch',
                default: frm.doc.student_batch_name
            },
            {
                fieldtype: 'Read Only',
                label: __('Payment Plan'),
                fieldname: 'payment_plan',
                default: frm.doc.payment_plan
            },
        ],
        primary_action_label: __('Submit'),
        primary_action: async function () {
            validateForm(frm, dialog);
            dialog.hide();
            frappe.call({
                method: "frappe.client.submit",
                args: {
                    "doctype": frm.doc.doctype,
                    "docname": frm.doc.name,
                    "doc": frm.doc
                },
                callback: async function (r) {
                    let res = await frappe.db.get_value("Fees", { "program_enrollment": frm.doc.name }, "name");
                    let url = `/app/fees/${res.message.name}`;
                    window.location.href = url;
                }
            })
        }
    });
    dialog.show();
}


function validateForm(frm, dialog) {
    let missingFields = [];
    if (!frm.doc.payment_plan) {
        missingFields.push('Payment Plan');
    }
    if (!frm.doc.program) {
        missingFields.push('Program');
    }
    if (!frm.doc.academic_year) {
        missingFields.push('Academic Year');
    }
    if (!frm.doc.student_batch_name) {
        missingFields.push('Student Batch');
    }

    if (missingFields.length > 0) {
        dialog.hide();
        frappe.msgprint({
            title: __('Missing Fields'),
            indicator: 'red',
            message: __('Please fill the following fields: ') + missingFields.join(', '),
            primary_action: {
                'label': 'Close',
                'action': function () {
                    frappe.hide_msgprint();
                }
            }
        });
        throw new Error('Missing fields: ' + missingFields.join(', '));
    }
}