// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
function addQuestionButton(frm) {
    frm.add_custom_button("Add Question", () => {

        const d = new frappe.ui.form.MultiSelectDialog({
            doctype: "Descriptive Question",
            target: frm,
            date_field: undefined,
            setters: {
                class_type: "1",
                parent_question: ""
            },
            // data_fields: data_fields,
            get_query: () => {
                return {
                    parent_question: ["is", "set"]
                }
            },
            // add_filters_group: 1,
            // allow_child_item_selection: opts.allow_child_item_selection,
            // child_fieldname: opts.child_fieldname,
            // child_columns: opts.child_columns,
            // size: opts.size,
            action: function (selections, args) {
                console.log(selections, args)
            },
        });

    })
}

function addCreateQuestionPaper(frm) {
    frm.add_custom_button("Add Question Paper", () => {
        if (!frm.doc.__islocal) {
            frappe.model.with_doctype('Descriptive Question Paper', function () {
                var new_doc = frappe.model.get_new_doc('Descriptive Question Paper');
                new_doc.descriptive_exam = frm.doc.name
                frappe.set_route('Form', new_doc.doctype, new_doc.name);
            });
        }
    })
}

frappe.ui.form.on("Descriptive Exam", {

    refresh(frm) {
        addQuestionButton(frm)
        addCreateQuestionPaper(frm)
        // frm.set_df_property('questions', 'cannot_add_rows', true);
        // frm.set_df_property('questions', 'cannot_delete_rows', true);
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
    },
});
