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


