frappe.ui.form.on('Assessment Plan', {
    "onload": function (frm) {
        get_textbooks(frm)
    },
    refresh: function (frm) {

        addFromDescriptiveExam(frm)

        frm.set_query("course", function () {
            return { filters: { "custom_hide_in_portion": 0 }, query: "" }
        })
        frm.set_query("assessment_group", function () {
            return { filters: { "custom_academic_year": frm.doc.academic_year } }
        })

    },

    academic_year: getAssessmentName,
    course: getAssessmentName,
    student_group: getAssessmentName,
    custom_type: getAssessmentName,
    assessment_group: getAssessmentName,
    custom_is_descriptive: addFromDescriptiveExam
})
async function getAssessmentName(frm) {

    if (!frm.doc.course || !frm.doc.student_group || !frm.doc.academic_year || !frm.doc.custom_type || !frm.doc.assessment_group) return
    if (frm.doc.__islocal) {
        frappe.call({
            method: "edu_quality.edu_quality.overrides.assessment_plan.name_func",
            args: {
                assessment_plan_doc: frm.doc
            }, callback: function (r) {
                frm.set_value('assessment_name', r.message)

            }
        })


    }
}
frappe.ui.form.on("Assessment Plan Criteria", {
    "assessment_criteria": function (frm, cdt, cdn) {
        checkDuplicates(frm, cdt, cdn)

    },
    "custom_exam_type": checkDuplicates,



})
function checkDuplicates(frm, cdt, cdn) {

    var d = locals[cdt][cdn];

    if (!d.assessment_criteria || !d.custom_exam_type) {
        return
    }
    frm.doc.assessment_criteria.forEach(function (row, i) {

        if ((row.assessment_criteria === d.assessment_criteria && row.custom_exam_type === d.custom_exam_type) && row.name != d.name) {

            frappe.msgprint(`Assesment Criteria/Exam Component Combination already exists for ${row.assessment_criteria}, ${row.custom_exam_type}`);
            frappe.model.remove_from_locals(cdt, cdn);
            frm.refresh_field('assessment_criteria');
            return false;
        }
    });
}

async function get_textbooks(frm) {
    const res = await frappe.call({
        method: "edu_quality.edu_quality.overrides.assessment_plan.get_assessment_cr_textbooks",

    })
    const data = [...res?.message, null] || [null]
    frm.set_df_property('custom_textbook', "options", data)
    frm.refresh_field("custom_textbook")
}

frappe.ui.form.on("Assessment Plan Criteria", {
    "custom_scale": function (frm, cdt, cdn) {
        console.log(frm, cdt, cdn)
        var d = locals[cdt][cdn];
        frm.doc.assessment_criteria.forEach(function (row, i) {

            if (row.custom_scale === 0 && row.name == d.name) {

                frappe.msgprint('0 Scale is not allowed, Setting it to 1');
                // frappe.model.remove_from_locals(cdt, cdn);
                frappe.model.set_value(cdt, cdn, "custom_scale", 1)
                frm.refresh_field('assessment_criteria');

                return false;
            }
        });
    }
})

function addFromDescriptiveExam(frm) {
    if (!frm.doc.custom_is_descriptive) { return }
    const d = new frappe.ui.Dialog({
        title: "Select a Exam Paper",
        fields: [
            {
                "fieldname": "exam",
                "label": __("Exam"),
                "fieldtype": "Link",
                "reqd": 1,
                options: "Descriptive Exam Paper"
            },

        ],
        primary_action: async (values) => {

            frappe.call({
                method: "edu_quality.edu_quality.overrides.assessment_plan.get_questions",
                type: "POST",
                args: {
                    paper: values.exam,
                },
                callback: function (data) {

                    if (data.message) {
                        let existing_values = new Set();

                        // Populate the set with existing child table values
                        frm.doc.assessment_criteria.forEach(function (row) {
                            let value = `${row.custom_question}`;
                            existing_values.add(value);
                        });

                        if (data && data.message) {
                            data.message.forEach(function (data) {
                                let new_value = `${data.custom_question}`;

                                if (existing_values.has(new_value)) return

                                let child_row = frm.add_child('assessment_criteria');

                                frappe.model.set_value(child_row.doctype, child_row.name, 'custom_question', data.custom_question);
                                frappe.model.set_value(child_row.doctype, child_row.name, 'custom_parent_question', data.custom_parent_question);
                                frappe.model.set_value(child_row.doctype, child_row.name, 'custom_scale', data.custom_scale);
                                frappe.model.set_value(child_row.doctype, child_row.name, 'assessment_criteria', data.assessment_criteria);
                                frappe.model.set_value(child_row.doctype, child_row.name, 'maximum_score', data.maximum_score);

                            });
                            frm.refresh_field('assessment_criteria');
                        }
                    }
                },

            })

        }
    })

    frm.add_custom_button("Add Question From Template", () => {
        d.show()
    })
}