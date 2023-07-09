// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Refund Request", {
	refresh(frm) {
        if (frappe.session.user == "Administrator"){
            if (frm.doc.approved === 0){
               frm.add_custom_button(__('Approve'), function(){
                   frappe.db.set_value("Refund Request", frm.doc.name, "approved", 1)
                   frappe.db.commit()
                   frm.remove_custom_button('Approve')
             });
           }
       }
	},
});
