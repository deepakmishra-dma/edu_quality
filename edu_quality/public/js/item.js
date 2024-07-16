async function getItemCode(frm) {
    if (!frm.doc.custom_subject || !frm.doc.custom_class || !frm.doc.custom_textbook || !frm.doc.custom_chapter || !frm.doc.item_group) return
    if (frm.doc.__islocal) {
        frappe.call({
            method: "edu_quality.overrides_hooks.item.calculate_sheet_number",
            args: {
                self: frm.doc
            }, callback: function (r) {
                frm.set_value('custom_sheet_number', r.message)
                frappe.call({
                    method: "edu_quality.overrides_hooks.item.name",
                    args: {
                        self: frm.doc
                    }, callback: function (r) {
                        frm.set_value('item_code', r.message)
                        frm.set_value('item_name', r.message)
                    }
                })
            }
        })


    }
}
function queryTextbook(frm) {
    frm.set_query("custom_textbook", function () {
        return {
            filters: {
                "subject": frm.doc.custom_subject,
                "class": frm.doc.custom_class
            }
        }
    })
}
function queryTopic(frm) {
    frm.set_query("custom_chapter", function () {
        return {
            filters: {
                "custom_subject": frm.doc.custom_subject,
                "custom_class": frm.doc.custom_class,
                "custom_textbook": frm.doc.custom_textbook
            }
        }
    })
}
function NotCmapFilter(frm) {
    frm.set_query("item_group", function () {
        return {
            "filters": {
                "parent_item_group": ["Not Like", "CMAP"],
                "name": ["Not Like", "CMAP"]
            }
        }
    })
}
frappe.ui.form.on("Item", {
    refresh: function (frm) {
        queryTextbook(frm)
        queryTopic(frm)
        if (!frm.doc.__islocal)
            frappe.call({
                method: "edu_quality.overrides_hooks.item.get_qr_code",
                args: {
                    name: frm.doc.name
                }, callback: function (r) {
                    frm.fields_dict.custom_qr_code_preview.wrapper.innerHTML = `<img src="${r.message}"/>
            `
                }
            })
        frm.get_field('custom_view_worksheet_header').onclick = function () {
            if (!frm.doc.__islocal) {

                window.open(`/api/method/edu_quality.overrides_hooks.item.get_worksheet_template?name=${frm.doc.name}`)

            }
        }
    },
    onload: function (frm) {
        if (frm.doc__islocal) {
            frm.set_value('custom_sheet_number', 0);
        } NotCmapFilter(frm);
    },
    custom_is_cmap: function (frm) {
        console.log(frm)
        if (frm.doc.custom_is_cmap === 1) {
            frm.set_query("item_group", function () {
                return {
                    "filters": {
                        "parent_item_group": "CMAP",

                    }
                }
            })
        }
        else {
            NotCmapFilter(frm)
        }
    },
    item_group: getItemCode,
    custom_chapter: getItemCode
    // item_group: function (frm) {
    //     console.log(frm.item_group, frm)
    //     if (frm.item_group.parent_item_group === "CMAP") {
    //         frm.set_value("custom_is_cmap", 1);
    //     }
    //     else {
    //         frm.set_value("custom_is_cmap", 0);
    //     }

    // }
});

