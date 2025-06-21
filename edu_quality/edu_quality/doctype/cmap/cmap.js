// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
async function getPeriodNo(frm, ignoreExistingValue = false) {
    if (!frm.doc.subject || !frm.doc.class || !frm.doc.academic_year) return
    if (frm.doc.__islocal || ignoreExistingValue) {
        if (ignoreExistingValue) {
            frm.set_value('period', '')
        }
        frappe.call({
            method: "edu_quality.edu_quality.doctype.cmap.cmap.get_cmap_period_no",
            args: {
                self: frm.doc
            }, callback: function (r) {
                // frm.set_value('custom_sheet_number', r.message)
                if (ignoreExistingValue || !frm.doc.period)
                    frm.set_value('period', r.message)
            }
        })


    }
}
async function getNoteQuery(cur_frm, fieldName, fieldGroup, options, item) {
    const field = frappe.meta.get_docfield("Item Detail", fieldName, item)
    field.options = options || [];

    cur_frm.refresh_field("products")
}
function updateNoteQuery(cur_frm, res, row_name) {
    const groups = [["broadcast", "Broadcast"], ["parent_note", "Parent Note"], ["home_work", "Home Work"], ["class_work", "Class Work"], ["material_required", "Material Required"]]
    if (res == "EMPTY_IT") {
        return groups.forEach(array => {
            getNoteQuery(cur_frm, array[0], array[1],
                [" "], row_name
            )
        })
    }

    return groups.forEach(array => {
        getNoteQuery(cur_frm, array[0], array[1],
            [...(res?.[array[1]] || [null])], row_name
        )
    })
}
async function setupNotesColumns(cur_frm) {

    const EXISTING_ROWS_IN_CHILD_TABLE = cur_frm.fields_dict["products"].grid.grid_rows

    for (row in EXISTING_ROWS_IN_CHILD_TABLE) {

        const item = frappe.model.get_value("Item Detail", EXISTING_ROWS_IN_CHILD_TABLE[row].doc.name, "item")
        const res = await getProductMaterials(item)
        updateNoteQuery(cur_frm, res?.message, EXISTING_ROWS_IN_CHILD_TABLE[row].doc.name)

    }
}

async function getProductMaterials(item) {
    const res = await frappe.call({
        method: "edu_quality.edu_quality.doctype.cmap.cmap.get_product_materials",
        args: {
            "item_id": item
        }
    })
    return res
}

async function getProduct(id) {
    const headers = new Headers()
    headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
    const res = await fetch(`/api/resource/Item/${id}?fields=["custom_additional_material"]`, {

        headers: headers,

    })
    const data = await res.json()
    return data.data.custom_additional_material
}
async function checkNotes(type, frm, materialType) {
    const broadcastItems = frm.fields_dict['products'].grid.data?.map(item => item[type]);
    const headers = new Headers()
    headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
    frappe.call({
        method: "edu_quality.edu_quality.doctype.cmap.cmap.check_if_note_added_unique",
        args: {
            "material_type": materialType,
            "added_items": broadcastItems
        },
        callback: function (r) {

        }
    });

}

async function getNotes(frm) {

}
async function getLinkedSubject(frm) {
    if (frm.doc.class)
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Class Type",
                name: frm.doc.class,
            },
            callback(r) {
                if (r.message) {
                    const classData = r.message;

                    const arrayOfSubjects = classData.subject.map(function (obj) {
                        return obj.subject;
                    });
                    frm.set_query("subject", function () {
                        return {
                            filters: [['name', 'in', arrayOfSubjects]]
                        }
                    })
                }
            }
        });



}
function texbookQuery(frm) {
    // frm.fields_dict['products'].grid.get_field('textbook').get_query = function (doc, cdt, dn) {
    //     let d = locals[cdt][dn];
    //     return {
    //         "filters": {
    //             "subject": cur_frm.doc.subject,
    //             "class": cur_frm.doc.class
    //         },

    //     };
    // }
}
frappe.ui.form.on("CMAP", {
    refresh(frm) {

        frm.set_query("academic_year", function () {
            return {
                "query": "edu_quality.edu_quality.doctype.cmap.cmap.get_current_and_next_year",


            }
        })
        getNotes(frm)
        cur_frm.fields_dict['products'].grid.get_field('item_group').get_query = function (doc, cdt, dn) {
            let d = locals[cdt][dn];
            return {
                "filters": {
                    "parent_item_group": `CMAP`,
                }
            };
        }
        cur_frm.fields_dict['products'].grid.get_field('item').get_query = function (doc, cdt, dn) {
            let d = locals[cdt][dn];
            return {
                "filters": {

                    "item_group": d.item_group,
                    "custom_chapter": d.chapter,
                    "custom_textbook": d.textbook,
                }
            };
        }
        cur_frm.fields_dict['products'].grid.get_field('chapter').get_query = function (doc, cdt, dn) {
            let d = locals[cdt][dn];
            return {
                "filters": {
                    "custom_textbook": d.textbook
                },

            };
        }
        texbookQuery(cur_frm)
        setupNotesColumns(cur_frm)
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
    class: (frm) => {
        getLinkedSubject(frm)
        getPeriodNo(frm)
        texbookQuery(frm)
    },
    unit: (frm) => {
        getPeriodNo(frm)
    },
    academic_year: (frm) => {
        getPeriodNo(frm)
    }
    , subject: (frm) => {
        getPeriodNo(frm)
        texbookQuery(frm)
    }
    , reserved_for_portion_circular: (frm) => {
        if (!frm.doc.reserved_for_portion_circular) {
            return getPeriodNo(frm, true)
        }
        getRandomString(frm)
    }


});

frappe.ui.form.on("Item Detail", {
    broadcast: async (frm) => {
        const res = await checkNotes("broadcast", frm, "Broadcast")

    },
    parent_note: async (frm) => {
        const res = await checkNotes("parent_note", frm, "Parent Note")
    },
    home_work: async (frm) => {
        const res = await checkNotes("home_work", frm, "Home Work")
    },
    class_work: async (frm) => {
        const res = await checkNotes("class_work", frm, "Class Work")
    },
    material_required: async (frm) => {
        const res = await checkNotes("material_required", frm, "Material Required")
    },
    item: async function (frm, cdt, cdn) {

        var d = locals[cdt][cdn];
        if (d.item) {
            const res = await getProductMaterials(d.item)
            updateNoteQuery(cur_frm, res?.message, d.name)
        }
        else {
            updateNoteQuery(cur_frm, "EMPTY_IT", d.name)
        }
        frm.doc.products.forEach(function (row, i) {

            if (row.item === d.item && row.name != d.name) {

                frappe.msgprint('Item you added already exists on the table.');
                frappe.model.remove_from_locals(cdt, cdn);
                frm.refresh_field('products');
                return false;
            }
        });
    }
})


async function getRandomString(frm) {
    if (!frm.doc.reserved_for_portion_circular) return

    frappe.call({
        method: "edu_quality.edu_quality.doctype.cmap.cmap.id_generator",
        callback: function (r) {
            frm.set_value('period', r.message)
        }
    })



}
