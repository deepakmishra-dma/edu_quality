// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("CBSE LOC", {
    before_workflow_action: function (frm) {
        let action = frm.selected_workflow_action;
        if (action === 'Reject') {
            let d = new frappe.ui.Dialog({
                title: 'Reason for Rejection',
                fields: [
                    {
                        fieldname: 'reason',
                        fieldtype: 'Data',
                        label: 'Reason for Rejection',
                        reqd: 1
                    }
                ],
                primary_action_label: 'Submit',
                primary_action(values) {
                    d.hide();
                    frappe.call({
                        doc: frm.doc,
                        method: 'reject',
                        args: {
                            reason: values.reason
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                frappe.show_alert('Rejected', 5);
                                frm.reload_doc();
                            }
                        }
                    });
                }
            });
            d.show();
        }
    },
});