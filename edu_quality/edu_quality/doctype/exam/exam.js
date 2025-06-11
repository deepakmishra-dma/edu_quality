// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Exam", {
    refresh(frm) {
        frm.set_query("class", function () {
            return {
                "filters":
                    [["class_group", "in", ["Primary", "Secondary"]], ["school", "=", frm.doc.school]],
            };
        })
    },
});
