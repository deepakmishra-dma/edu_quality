// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
function queryTextbook(frm) {
    frm.set_query("texbook", function () {
        return {
            filters: {
                "subject": frm.doc.subject,
                "class": frm.doc.class
            }
        }
    })
}
function queryTopic(frm) {
    frm.set_query("chapter", function () {
        return {
            filters: {
                "custom_subject": frm.doc.subject,
                "custom_class": frm.doc.class,
                "custom_textbook": frm.doc.texbook
            }
        }
    })
}
frappe.ui.form.on("CMAP", {
    refresh(frm) {
        queryTextbook(frm)
        queryTopic(frm)
        cur_frm.fields_dict['products'].grid.get_field('item_group').get_query = function (doc, cdt, dn) {
            let d = locals[cdt][dn];

            return {
                "filters": {
                    "parent_item_group": `CMAP`,
                }
            };
        }
        cur_frm.fields_dict['table_vwbr'].grid.get_field('division').get_query = function (doc, cdt, dn) {
            let d = locals[cdt][dn];

            return {
                "filters": {
                    "program": `${frm.doc.class}-${d.school}`,
                    "academic_year": `${frm.doc.academic_year}`
                }
            };
        }
    },


});
