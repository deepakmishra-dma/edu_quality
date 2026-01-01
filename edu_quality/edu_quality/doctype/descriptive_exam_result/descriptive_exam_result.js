// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Descriptive Exam Result", {
    refresh(frm) {
        frm.set_query("academic_year", function () {
            return {
                "query": "edu_quality.public.py.utils.academic_year_query"
            };
        })
    },

    academic_year: function (frm) {
        frm.set_query("student_group", function () {
            return {
                "filters": {
                    "academic_year": frm.doc.academic_year,

                }
            };
        })
    }
    ,
    school: function (frm) {
        frm.set_query("program", function () {
            return {
                "filters": {
                    "school": frm.doc.school,
                }
            };
        })
    },
    program: function (frm) {
        frm.set_query("student_group", function () {
            return {
                "filters": {
                    "program": frm.doc.program,
                    "custom_school": frm.doc.school,
                }
            };
        })

        frm.set_query("descriptive_exam", function () {
            return {
                "filters": {
                    "program": frm.doc.program,
                    "custom_school": frm.doc.school,
                }
            };
        })
    },
    "student_group": function (frm) {
        frm.set_query("descriptive_exam", function () {
            return {
                "filters": {
                    "program": frm.doc.program,
                    "custom_school": frm.doc.school,
                    "student_group": frm.doc.student_group
                }
            };
        })
    }
});
