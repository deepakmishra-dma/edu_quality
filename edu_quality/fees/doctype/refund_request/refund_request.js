// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Refund Request", {
    refresh(frm) {
        if (frappe.session.user == "Administrator") {
            if (frm.doc.approved === 0) {
                frm.add_custom_button(__('Approve'), function () {
                    if (frm.doc.refundable_after > frappe.datetime.get_today()) {
                        frappe.msgprint({
                            title: __('Not Approved'),
                            message: __("Refundable After Date is not reached"),
                            indicator: 'red'
                        });
                        return
                    }else{
                        frappe.db.set_value("Refund Request", frm.doc.name, "approved", 1)
                        frm.remove_custom_button('Approve')
                        frm.refresh()
                    }
                });
            }
        }
        frm.set_query("pending_fees", function() {
            return {
                "filters": {
                    "student": frm.doc.student_id
                }
            };
        });
    },
});
