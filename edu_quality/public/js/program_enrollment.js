frappe.ui.form.on("Program Enrollment", {
    refresh: function (frm) {
        if (!frm.is_new() && frm.doc.docstatus === 0) {
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
    },

    create_fees: function (frm) {
        showPopup(frm);
    }
});


function showPopup(frm){
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
        primary_action: async function() {
            dialog.hide();
            frappe.call({
                method: "frappe.client.submit",
                args: {
                      "doctype": frm.doc.doctype,
                      "docname": frm.doc.name,
                      "doc": frm.doc
                },
                callback: async function (r) {
                    let res = await frappe.db.get_value("Fees", {"program_enrollment": frm.doc.name}, "name");
                    let url = `/app/fees/${res.message.name}`;
                    window.open(url, '_blank');
                }
            })
        }
    });
    dialog.show();
}