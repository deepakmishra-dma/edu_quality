// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
var sd;
function addQuestionButton(frm) {
    frm.add_custom_button("Add Question", () => {

        const d = new frappe.ui.form.MultiSelectDialog({
            doctype: "Descriptive Question",
            target: frm,
            date_field: undefined,
            setters: [{
                fieldname: "class_type",
                default: frm.doc.class_type,
                label: "Class Type",
                fieldtype: "Link",
                "options": "Class Type"
                // parent_question: ""
            },
            {
                fieldname: "parent_descriptive_question",

                label: "Parent Question",
                fieldtype: "Link",
                "options": "Descriptive Question"
                // parent_question: ""
            }],
            // data_fields: data_fields,
            get_query: () => {
                return {
                    parent_question: ["is", "not_set"]
                }
            },
            add_filters_group: 1,
            // allow_child_item_selection: opts.allow_child_item_selection,
            // child_fieldname: opts.child_fieldname,
            // child_columns: opts.child_columns,
            // size: opts.size,
            action: async function (selections, args) {
                const data = await frappe.call({
                    "method": "edu_quality.edu_quality.doctype.descriptive_exam_paper.descriptive_exam_paper.add_question",
                    args: {
                        docnames: selections
                    }
                });
                let existing_values = new Set();

                // Populate the set with existing child table values
                frm.doc.questions.forEach(function (row) {
                    let value = `${row.question}`;
                    existing_values.add(value);
                });

                if (data && data.message) {
                    data.message.forEach(function (data) {
                        let new_value = `${data.name}`;

                        if (existing_values.has(new_value)) return
                        let child_row = frm.add_child('questions');

                        frappe.model.set_value(child_row.doctype, child_row.name, 'question', data.name);
                        frappe.model.set_value(child_row.doctype, child_row.name, 'parent_question', data.parent_descriptive_question);
                        frappe.model.set_value(child_row.doctype, child_row.name, 'selected', 1)
                    });
                    frm.refresh_field('questions');
                }
            },
        });
        setTimeout(() => {
            d.filter_group.add_filter("Descriptive Question", "parent_descriptive_question", "is", "not set");
            setTimeout(() => {
                if (d.is_child_selection_enabled()) {
                    d.show_child_results();
                } else {
                    d.get_results();
                }
            }, 1000)
        }, 1000)

    })
}

// function addCreateQuestionPaper(frm) {
//     frm.add_custom_button("Add Question Paper", () => {
//         if (!frm.doc.__islocal) {
//             frappe.model.with_doctype('Descriptive Question Paper', function () {
//                 var new_doc = frappe.model.get_new_doc('Descriptive Question Paper');
//                 new_doc.descriptive_exam = frm.doc.name
//                 frappe.set_route('Form', new_doc.doctype, new_doc.name);
//             });
//         }
//     })
// }

frappe.ui.form.on("Descriptive Exam Paper", {

    refresh(frm) {
        addQuestionButton(frm)
        // addCreateQuestionPaper(frm) 
        // frm.set_df_property('questions', 'cannot_add_rows', true);
        frm.set_df_property('questions', 'cannot_delete_rows', true);
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
