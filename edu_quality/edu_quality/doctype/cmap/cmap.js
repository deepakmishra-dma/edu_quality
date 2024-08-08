// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
async function getPeriodNo(frm) {
    if (!frm.doc.subject || !frm.doc.class || !frm.doc.academic_year) return
    if (frm.doc.__islocal) {
        frappe.call({
            method: "edu_quality.edu_quality.doctype.cmap.cmap.get_cmap_period_no",
            args: {
                self: frm.doc
            }, callback: function (r) {
                // frm.set_value('custom_sheet_number', r.message)
                if (!frm.doc.period)
                    frm.set_value('period', r.message)
            }
        })


    }
}
function getNoteQuery(cur_frm, fieldName, fieldGroup) {

    cur_frm.fields_dict['products'].grid.get_field(fieldName).on_change = function () {

    }
    cur_frm.fields_dict['products'].grid.get_field(fieldName).get_query = function (doc, cdt, dn) {
        let d = locals[cdt][dn];
        return {
            "query": "edu_quality.edu_quality.doctype.cmap.cmap.get_unique_material_query",
            "filters": {
                "parent": d.item,
                "material_type": fieldGroup,

            },
        };
    }
}
function setupNotesColumns(cur_frm) {
    const groups = [["broadcast", "Broadcast"], ["parent_note", "Parent Note"], ["home_work", "Home Work"], ["class_work", "Class Work"], ["material_required", "Material Required"]]
    groups.forEach(array => {
        getNoteQuery(cur_frm, array[0], array[1])
    })
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
            console.log(r.message)
        }
    });

}

async function getNotes(frm) {
    // const products = frm.get_field('products').grid.data || []
    // const data = await Promise.all(products.map(product => {
    //     return getProduct(product.item)
    // }))
    // let optionsHash = {}

    // data.forEach(el => {
    //     el.forEach(note => {
    //         if (Array.isArray(optionsHash[note.material_type])) {
    //             optionsHash[note.material_type].push(note.description)
    //         }
    //         else {
    //             optionsHash[note.material_type] = [note.description]
    //         }
    //     })
    // })
    // const broadcast = frm.get_field('broadcast')
    // const homeWork = frm.get_field('home_work')
    // const classWork = frm.get_field("class_work")
    // const materialRequired = frm.get_field("material_required")
    // const parentNote = frm.get_field("parent_note")
    // broadcast.df.options = optionsHash['Broadcast'] || []
    // homeWork.df.options = optionsHash['Home Work'] || []
    // parentNote.df.options = optionsHash['Parent Note'] || []
    // classWork.df.options = optionsHash['Class Work'] || []
    // materialRequired.df.options = optionsHash['Material Required'] || []
    // broadcast.set_options()
    // homeWork.set_options()
    // classWork.set_options()
    // materialRequired.set_options()
    // parentNote.set_options()
}
frappe.ui.form.on("CMAP", {
    refresh(frm) {
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
        getPeriodNo(frm)
    },
    unit: (frm) => {
        getPeriodNo(frm)
    },
    academic_year: (frm) => {
        getPeriodNo(frm)
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

})



