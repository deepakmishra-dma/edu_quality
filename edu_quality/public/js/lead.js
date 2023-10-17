var error_msg = {
    "academic_year": "Academic Year is required before pushing to MGR",
    "center": "School is required before pushing to MGR",
    "first_name": "First name is required before pushing to MGR",
    "fathers_phone": "Father's phone number is required before pushing to MGR",
    "class": "Class is required before pushing to MGR",
    "fathers_email": "father's email id is required before pushing to MGR",
    "gender": "Gender is required before pushing to MGR",

}

var subStatuses = {
    'fresh': ["Not Known", "Online Enquiry", "Telephonic Enquiry", "Walkin Enquiry"],
    'warm': ["Center Visit Planned", "School Visit Done"],
    'followup/callback': ["Call back later",
        "Call not answering",
        "Curious",
        "Interaction Done",
        "Not Reachable",
        "School Visit Done",
        "Switched Off",
        "Trial Class",],
    "hot": ["Followup for Enrollment", "Interested-Will Enroll", "School Visit Done"]
    , "cold": ["Added in Waiting List", "Enrolled in another school", "Fees High", "Junk/Invalid", "Location not Convenient", "Rejected", "Schedule not Convenient", "School Visit Done"],
    "enrolled": ["Admission Taken"],
    "existing parents": ["Already Enrolled"],
    "old leads": ['Old lead'],
    "closed": ['zxc']
}

frappe.ui.form.on("Lead", {
    refresh: function (frm) {
        setTimeout(() => {
            frm.clear_custom_buttons()




            frm.add_custom_button(__("Push To MGR"), function () {
                var errorKey = Object.keys(error_msg).find(error => frm.doc[error] === null || frm.doc[error] === undefined || frm.doc[error] === '')
                if (errorKey) {
                    frappe.msgprint({
                        title: __('Error'),
                        message: __(error_msg[errorKey]),
                        indicator: 'red'
                    });
                    return
                }

                frappe.call({
                    method: "edu_quality.api.student_application.create_student_application",
                    type: "POST",
                    args: { name: frm.docname },
                });
            })
            $('.inner-group-button[data-label="Create"]').remove()
        }, 10)

        if (frm.doc.status)
            frm.set_df_property("lead_sub_status", "options", subStatuses[frm.doc.status.toLowerCase()])
        $("textarea[data-fieldname='custom_cold_comment'],textarea[data-fieldname='overall_remarks'],textarea[data-fieldname='follow_up_comment'],textarea[data-fieldname='walk_in_1'],textarea[data-fieldname='walk_in_2'],textarea[data-fieldname='walk_in_3']").css({ 'height': '70' });

    },


    center: function (frm) {

        frm.set_query("class", function () {
            return {
                "filters": {
                    "school": frm.doc.center
                }
            };
        });
    },
    status: function (frm) {

        frm.set_query("custom_lead_sub_status", function () {
            return {
                "filters": {
                    "type": frm.doc.status
                }
            };
        });
    }
});


