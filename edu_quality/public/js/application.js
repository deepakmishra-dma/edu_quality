frappe.ui.form.on("Student Applicant", {

	refresh: function(frm) {
        if(frm.doc.paid === 0){
            frm.remove_custom_button("Enroll");
        }
    }
});