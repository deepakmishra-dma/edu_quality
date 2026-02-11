// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Assessment Group Result", {
    refresh(frm) {
        frm.set_intro(`
            <p class="text-dark my-0">
                Only Marks scoring type is considered, when calculating class rank and if one of them have a criteria with online assessment it is discarded
          `, 'blue')
    },
});
