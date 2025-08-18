frappe.ui.form.on('Assessment Plan', {
    refresh: function (frm) {
        frm.set_query("course", function () {
            return { filters: { "custom_hide_in_portion": 0 }, query: "" }
        })
        get_textbooks(frm)
    },

    academic_year: getAssessmentName,
    course: getAssessmentName,
    student_group: getAssessmentName,
    custom_type: getAssessmentName,
    assessment_group: getAssessmentName
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
        get_textbooks(frm)
    },
    "custom_exam_type": checkDuplicates,
    "custom_textbook": checkDuplicates,


})
function checkDuplicates(frm, cdt, cdn) {

    var d = locals[cdt][cdn];

    if (!d.custom_textbook || !d.assessment_criteria || !d.custom_exam_type) {
        return
    }
    frm.doc.assessment_criteria.forEach(function (row, i) {
        const all_textbooks = d.custom_textbook == "All"
        if (((all_textbooks || d.custom_textbook == row.custom_textbook) && row.assessment_criteria === d.assessment_criteria && row.custom_exam_type === d.custom_exam_type) && row.name != d.name) {

            frappe.msgprint(`Assesment Criteria/Exam Component Combination already exists for ${row.custom_textbook}, ${row.assessment_criteria}, ${row.custom_exam_type}`);
            frappe.model.remove_from_locals(cdt, cdn);
            frm.refresh_field('assessment_criteria');
            return false;
        }
    });
}

async function get_textbooks(frm) {

    const EXISTING_ROWS_IN_CHILD_TABLE = cur_frm.fields_dict["assessment_criteria"].grid.grid_rows
    const res = await frappe.call({
        method: "edu_quality.edu_quality.overrides.assessment_plan.get_assessment_cr_textbooks",

    })
    for (row in EXISTING_ROWS_IN_CHILD_TABLE) {

        const res = await frappe.call({
            method: "edu_quality.edu_quality.overrides.assessment_plan.get_assessment_cr_textbooks",

        })


        const field = frappe.meta.get_docfield("Assessment Plan Criteria", "custom_textbook", EXISTING_ROWS_IN_CHILD_TABLE[row].doc.name)

        frm.fields_dict.assessment_criteria.grid.update_docfield_property("custom_textbook", "options", res?.message)
        console.log(row, EXISTING_ROWS_IN_CHILD_TABLE[row].doc.name)
        field.options = [null, ...res?.message] || [null];
        // field.set_options([null, ...res?.message] || [null])
        cur_frm.refresh_field("assessment_criteria")
        // cur_frm.refresh()
    }


}