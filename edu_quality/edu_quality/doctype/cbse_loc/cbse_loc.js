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
    
    refresh: function (frm) {
        frm.add_custom_button(__('Check Updated Field'), function () {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Version',
                    filters: {
                        ref_doctype: frm.doc.doctype,
                        docname: frm.doc.name
                    },
                    order_by: 'creation desc',
                    limit: 1
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        var version = r.message[0];
                        frappe.set_route('Form', 'Version', version.name);
                    } else {
                        frappe.msgprint(__('No versions found'));
                    }
                }
            });
        });
    }
});