// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company", {
    refresh(frm) {
        const setCommonQuery = (field) => {
            frm.set_query(field, function() {
                return {
                    filters: {
                        company: frm.doc.name,
                        is_group: 0
                    }
                };
            });
        };

        // Apply the query to all relevant fields
        const fields = [
            'default_petty_cash',
            'default_petty_cash_bank',
            'custom_easebuzz_charges',
            'default_easebuzz_account',
            'default_liability_account',
            'custom_default_concession_account'
        ];

        fields.forEach(setCommonQuery);
    },
});
