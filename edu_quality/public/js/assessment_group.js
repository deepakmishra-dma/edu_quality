frappe.ui.form.on('Assessment Group', {
    is_group: (frm) => {
        if (frm.doc.is_group == 0)
            frm.set_field("custom_is_composite", 0)
    },
    refresh: (frm) => {
        cur_frm.fields_dict['custom_composite_exams'].grid.get_field('assesment_group').get_query = function (doc, cdt, dn) {
            let d = locals[cdt][dn];
            return {
                "filters": {
                    "is_group": 0,
                    "custom_is_composite": 0,
                }
            };
        }
    }
})
