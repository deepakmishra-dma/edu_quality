// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Event", {
    refresh(frm) {
        frm.set_query('class', "custom_classes", function (doc, cdt, cdn) {
            return {
                "filters": {
                    "school": doc.custom_branch,
                }
            };
        });
    },
});