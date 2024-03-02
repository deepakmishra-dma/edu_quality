
// import DataTable from "frappe-datatable";

// window.DataTable = DataTable;

function generateColumns(columns) {
    const generatedColumn = []

    columns.forEach((column) => {
        generatedColumn.push({
            ...column, format: (value, row, column, data) => { console.log(value, row, column, data); return value }
        })
    })
    return generatedColumn
}
frappe.ui.form.on('Purchase Order', {
    refresh(frm) {
        // your code here
        frappe.call({
            method: "edu_quality.overrides_hooks.purchase_order.generate_html_table",
            args: {
                self: frm.doc
            }, callback: function (r) {
                if (r.message) {
                    const challan_html = frm.get_field('custom_challan_detail');
                    columns = generateColumns(r.message[1])
                    data = r.message[2]

                    const datatable = new DataTable(frm.fields_dict.custom_challan_detail.wrapper, { columns, data, checkboxColumn: true });
                    console.log(datatable.rowmanager.getCheckedRows(), 'ha')
                    // challan_html.df.options = r.message[0]
                    // challan_html.set_options()
                }

            }
        })
    }
})
