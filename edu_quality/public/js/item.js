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
    refresh:function(frm){
        queryTextbook(frm)
        queryTopic(frm)
    },
    onload: NotCmapFilter,
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

