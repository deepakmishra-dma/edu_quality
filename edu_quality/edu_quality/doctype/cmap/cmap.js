// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
function queryTextbook(frm) {
    frm.set_query("texbook", function () {
        return {
            filters: {
                "subject": frm.doc.subject,
            }
        }
    })
}
function queryTopic(frm) {
    frm.set_query("chapter", function () {
        return {
            filters: {
                "custom_subject": frm.doc.subject,
                "custom_textbook": frm.doc.texbook
            }
        }
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
async function getNotes(frm) {
    const products = frm.get_field('products').grid.data || []
    const data = await Promise.all(products.map(product => {
        return getProduct(product.item)
    }))
    let optionsHash = {}

    data.forEach(el => {
        el.forEach(note => {
            if (Array.isArray(optionsHash[note.material_type])) {
                optionsHash[note.material_type].push(note.description)
            }
            else {
                optionsHash[note.material_type] = [note.description]
            }
        })
    })
    const broadcast = frm.get_field('broadcast')
    const homeWork = frm.get_field('home_work')
    const classWork = frm.get_field("class_work")
    const materialRequired = frm.get_field("material_required")
    const parentNote = frm.get_field("parent_note")
    broadcast.df.options = optionsHash['Broadcast'] || []
    homeWork.df.options = optionsHash['Home Work'] || []
    parentNote.df.options = optionsHash['Parent Note'] || []
    classWork.df.options = optionsHash['Class Work'] || []
    materialRequired.df.options = optionsHash['Material Required'] || []
    broadcast.set_options()
    homeWork.set_options()
    classWork.set_options()
    materialRequired.set_options()
    parentNote.set_options()
}
frappe.ui.form.on("CMAP", {
    refresh(frm) {
        getNotes(frm)
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
        cur_frm.fields_dict['products'].grid.get_field('item').get_query = function (doc, cdt, dn) {
            let d = locals[cdt][dn];
            return {
                "filters": {

                    "item_group": d.item_group
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
