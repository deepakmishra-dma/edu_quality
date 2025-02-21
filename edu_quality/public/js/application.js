frappe.ui.form.on("Student Applicant", {

    refresh: function (frm) {
        frm.remove_custom_button("Approve", "Actions")
        if (!frm.is_new() && frm.doc.application_status === "Applied") {
            frm.set_value("application_status", "Approved");
            frm.save_or_update();
            frm.add_custom_button(__("Enroll"), function () {
                frm.events.enroll(frm)
            }).addClass("btn-primary");
        }
        frappe.realtime.on("enroll_student_progress", function (data) {
            if (data.progress) {
                frappe.hide_msgprint(true);
                frappe.show_progress(__("Enrolling student"), data.progress[0], data.progress[1]);
            }
        });
    },

    enroll: function (frm) {
        frappe.call({
            method: "edu_quality.public.py.application.enroll_student",
            args: {
                "source_name": frm.docname
            },
            callback: function (r) {
                frappe.msgprint("Enrolled Successfully");
                if(r.message){
                    window.open(r.message, '_blank');
                }
                location.reload();

            }
        });
    }
});