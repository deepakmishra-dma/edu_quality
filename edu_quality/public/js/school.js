// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("School", {
    refresh(frm) {
        if (frm.doc.institution) {
            frm.set_query("event_account", function () {
                return {
                    filters: {
                        company: frm.doc.institution,
                        is_group: 0
                    }
                };
            });
            frm.set_query("petty_cash_bank_account", function () {
                return {
                    filters: {
                        company: frm.doc.institution,
                        is_group: 0
                    }
                };
            });
            frm.set_query("petty_cash_account", function () {
                return {
                    filters: {
                        company: frm.doc.institution,
                        is_group: 0
                    }
                };
            });
        }
    },
});
