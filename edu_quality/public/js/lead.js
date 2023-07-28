
frappe.ui.form.on("Lead", {
    refresh:function(frm){
        setTimeout(()=>{
            frm.remove_custom_button('Add to Prospect', 'Action')
            frm.remove_custom_button('Customer','Opportunity','Quotation','Prospect','Create');
            frm.add_custom_button(__("Push To MGR"), function() {
                frappe.call({
        method:"edu_quality.api.student_application.create_student_application",
        type: "POST",
        args: {name:frm.docname},
    });
            })
    },10)
    }

})