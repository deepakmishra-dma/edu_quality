frappe.ui.form.on("Instructor", {
    refresh: function (frm) {
        frm.set_query("course", "instructor_log", function (_doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {


            };
        });
        frm.set_query("student_group", "instructor_log", function (_doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            return {
                filters: {
                    program: d.program
                },

            };
        });
    }
});
