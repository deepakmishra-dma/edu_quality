frappe.ui.form.on('Assessment Plan', {
    refresh: function (frm) {
        frm.set_query("course", function () {
            return { filters: {}, query: "" }
        })
    }
})
