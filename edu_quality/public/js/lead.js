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
        if (frm.doc.status === "Hot" && frm.doc.custom_re_enquired_count) {
            frm.page.set_indicator('Hot ' + frm.doc.custom_re_enquired_count, "orange")
        }
        frm.set_intro(`
        <p class="text-dark my-0">
            Pushing to MGR requires these fields:<ul><li>Academic Year</li><li> School</li><li>First Name</li><li>Date of Birth</li><li>Fathers Phone</li><li>Class</li><li>Fathers Email</li><li>Gender</li>
      
      `, 'orange')
        setTimeout(() => {
            frm.clear_custom_buttons()

            // <div style="display:flex;align-items:center;gap:4px;"><img alt="open whatsapp ui" src="/assets/edu_quality/img/whatsapp-icon.png" style="height:100%;object-fit:contain;background-repeat:no-repeat;max-height:19.5px" /><div>Open in Whatsapp UI</div></div>`
            frm.add_custom_button(__(`Open in Whatsapp UI`), function () {
                frappe.call({
                    "method": "frappe.desk.form.linked_with.get",
                    args: {
                        docname: frm.doc.name,
                        doctype: "Lead"
                    }, callback: (data) => {
                        if (data?.message && data.message.Contact && data.message.Contact?.[0]?.name) {
                            window.location.href = window.location.origin + "/app/whatsapp_manager?user=" + data.message.Contact?.[0]?.name
                        }
                    }
                })
            }, '', "Open in whatsapp ui")

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
                    method: "frappe.desk.form.save.savedocs",
                    args: { doc: frm.doc, action: 'Save' },
                    callback: function (r) {
                        $(document).trigger("save", [frm.doc]);
                        frappe.call({
                            method: "edu_quality.api.student_application.create_student_application",
                            type: "POST",
                            args: { name: frm.docname },
                            callback: () => {
                                frm.disable_form()
                                frm.disable_save()
                            }
                        });
                    },
                    error: function (r) {
                    },
                });

            })
            $('.inner-group-button[data-label="Create"]').remove()
        }, 10)

        $("textarea[data-fieldname='custom_cold_comment'],textarea[data-fieldname='overall_remarks'],textarea[data-fieldname='follow_up_comment'],textarea[data-fieldname='walk_in_1'],textarea[data-fieldname='walk_in_2'],textarea[data-fieldname='walk_in_3']").css({ 'height': '70' });

    },

    validate: function (frm) {
        const re = /^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$/
        if (!re.test(frm.doc.fathers_phone)) {
            frappe.validated = false
        }
        if (frm.doc.next_action_date) {
            const date = new Date(frm.doc.next_action_date)
            if (date !== "Invalid Date" && date.getDay() === 0) {
                frappe.validated = false
                frappe.msgprint({
                    message: __("Next Action Date cannot be set to fall on Sunday"),
                    indicator: "red",
                    title: __("Incorrect Field")
                });
            }
        }
        return true
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


