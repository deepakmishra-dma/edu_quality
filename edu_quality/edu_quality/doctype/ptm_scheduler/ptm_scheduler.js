// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("PTM Scheduler", {
	refresh(frm) {
        if(!frm.doc.is_gmeet_generated){
            // frm.add_custom_button('Generate Gmeet',()=>{
            //     console.log('Generated')
            // }).addClass("btn-primary");
        }
	},
    teacher_alias: function(frm){
        if(frm.doc.teacher_alias){
            frappe.call({
                doc: frm.doc,
                method: "get_teacher",
                callback: function(r){
                    if(r.message){
                        frm.set_value('teacher', r.message);
                    }
                }
            });
        }
    }
});
