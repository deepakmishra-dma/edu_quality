frappe.ui.form.on("Student Applicant", {

    onload: function (frm) {
        frm.remove_custom_button("Approve", "Actions")
        frm.remove_custom_button("Enroll")
    },

    refresh: function (frm) {
        frm.remove_custom_button("Approve", "Actions")
        frm.remove_custom_button("Enroll")
        if (!frm.is_new() && frm.doc.application_status === "Applied") {
            frm.set_value("application_status", "Approved");
            frm.save_or_update();
        } else if (frm.doc.application_status === "Approved") {
            if (checkFields(frm)) {
                frm.add_custom_button(__("Enroll"), function () {
                    frappe.confirm('Are you sure you want to proceed?',
                        () => {
                            frappe.show_alert({
                                message: __('Student Enrolling...'),
                                indicator: 'green'
                            });
                            frm.remove_custom_button("Enroll")
                            frm.events.enroll(frm)
                        }, () => {
                            frappe.show_alert({
                                message: __('Action Cancelled'),
                                indicator: 'orange'
                            });
                        }) 
                }).addClass("btn-primary");
            } else {
                frm.remove_custom_button("Enroll")
            }
        }
    },

    enroll: function (frm) {
        frappe.realtime.on("enroll_student_progress", function (data) {
            if (data.progress) {
                frappe.hide_msgprint(true);
                frappe.show_progress(__("Enrolling student"), data.progress[0], data.progress[1]);
            }
        });
        frappe.call({
            method: "edu_quality.public.py.application.enroll_student",
            args: {
                "source_name": frm.docname
            },
            callback: function (r) {
                if (r.message) {
                    window.location.href = r.message;
                }
            }
        });
    }
});

function checkFields(frm) {
    if (frm.doc.school && frm.doc.program && frm.doc.academic_year && frm.doc.batch) {
        return true;
    } else {
        return false;
    }
}