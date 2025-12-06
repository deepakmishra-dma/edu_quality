// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Online Exam Submission", {
    refresh(frm) {
        frm.add_custom_button(__('Enter Marks'), async function () {
            const res = await frappe.db.get_value('Student Group', { 'program': frm.doc.classs, "student_group_name": frm.doc.division, academic_year: frm.doc.academic_year }, 'name')
            if (!res || !res.message || !res.message.name) {
                frappe.msgprint({
                    title: __('Error'),
                    indicator: 'red',
                    message: __('An error occurred while getting division')
                });
                return
            }
            const division = res.message.name
            frappe.call({
                method: "frappe.desk.form.save.savedocs",
                args: { doc: frm.doc, action: 'Save' },
                callback: function (r) {

                    frappe.set_route("query-report", "Marks Entry Tool", {
                        academic_year: frm.doc.academic_year,
                        school: frm.doc.school,
                        program: frm.doc.classs,
                        assessment_group: frm.doc.select_unit,
                        division: division,
                        mode: 1,
                        ref_no: frm.doc.student
                    })
                }
            })


        });
    },
});
