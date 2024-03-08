
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

async function getSchools() {
    const schools = await frappe.db.get_list('School', { fields: ["warehouse", "name"] })
    return schools.reduce((prev, curr) => { return { ...prev, [curr.name]: curr.warehouse } }, {})
}
function generateOrderCard(itemCode, totalQty, chapter, subject) {

    return `<div
                  style="
                    border-radius: var(--border-radius-md);
                    border: 1px solid var(--border-color);
                    box-shadow: none;
                    background-color: var(--card-bg);
                    padding:8px 12px;
                  "
                >
                <div style="display:flex;gap:4px;"><div>
                <div style="display:flex;gap:8px;">
                  <div style="font-weight: normal; border-radius: var(--border-radius-sm); background-color: var(--subtle-fg);width:150px;padding:4px;">${itemCode}</div>
                  <div style="font-weight: normal; border-radius: var(--border-radius-sm); background-color: var(--subtle-fg);width:100px;padding:4px;"><i class="fa fa-shopping-cart"></i> ${totalQty}</div>
                  </div>
                  <div style="margin-top:8px;margin-bottom:8px">${subject}</div>
                  <div>${chapter}</div>
                  <div >
                  <input data-item-code="${itemCode}"  type="checkbox" style="width:22px !important;height:22px;flex-shrink:0;margin-top:8px;" ></input></div> 
                  </div></div>
                </div>`
}
function getCheckedItems(frm) {
    const inputsList = Array.from(frm.fields_dict.custom_challan_detail.wrapper.querySelectorAll("input[type='checkbox']"))
    return inputsList.filter((elem) => {
        return elem.checked
    }).map(elem => elem.dataset.itemCode)
}
function createReceiptButton(frm) {
    if ((frappe.user_roles.includes("Printer") || frappe.user_roles.includes("Administrator") || frappe.user_roles.includes("Walnut Admin") ||
        frappe.user_roles.includes("System_Manager")))
        frm.add_custom_button(__('Create Receipts'), async function () {
            var d = new frappe.ui.Dialog({
                title: 'New Purchase Receipts',
                fields: [{
                    label: 'School',
                    fieldname: 'school',
                    fieldtype: 'Link',
                    options: "School",
                    reqd: true
                },
                {
                    label: "Challan Details",
                    fieldname: 'challan_table',
                    fieldtype: 'HTML',
                    options: "School",
                    read_only: true
                }],
                primary_action_label: 'Create',
                async primary_action(values) {

                    frappe.call({
                        method: 'edu_quality.overrides_hooks.purchase_order.create_purchase_receipt',
                        args: {
                            self: frm.doc,
                            school: values.school,
                            selected_items: getCheckedItems(frm)
                        },
                        callback: (r) => {
                            if (r.message) {
                                frappe.msgprint({
                                    indicator: "green",
                                    title: __("Created Successfully"),
                                    message: __(
                                        "Receipt Created Successfully"
                                    ),
                                });
                            }
                        }
                    })



                },
            })
            const schools = await getSchools()

            d.fields_dict.school.input.addEventListener('input', async (e) => {
                if (schools[d.fields_dict.school.input.value]) {
                    const checkedItems = getCheckedItems(frm)
                    const tableItems = await frappe.db.get_list("Purchase Order Item", { filters: [["parent", "=", frm.doc.name], ["item_code", "in", checkedItems], ["warehouse", "=", schools[d.fields_dict.school.input.value]]], fields: ["name", "qty", "item_name"] })
                    const data = tableItems.map((item) => ([null, item.qty]))
                    new DataTable(d.fields_dict.challan_table.wrapper, {
                        columns: ['Item Code', 'Quantity'],
                        data: data
                    })
                }
            })
            d.fields_dict.school.wrapper.querySelector('ul').addEventListener('click', (e) => {
                console.log(e)
                new DataTable(d.fields_dict.challan_table.wrapper, {
                    columns: ['Item Code', 'Quantity'],
                    data: [
                        ['Faris', 'Software Developer'],
                        ['Manas', 'Software Engineer',],
                    ]
                })
            })
            // setTimeout(() => {
            //     new DataTable(d.fields_dict.challan_table.wrapper, {
            //         columns: ['Name', 'Position', 'Salary'],
            //         data: [
            //             ['Faris', 'Software Developer', '$1200'],
            //             ['Manas', 'Software Engineer', '$1400'],
            //         ]
            //     });
            // }, 1000)
            d.show()
        })
}

function removeBtnsForPrinters(frm) {
    if ((frappe.user_roles.includes("Printer") && !frappe.user_roles.includes("Administrator") && !frappe.user_roles.includes("Walnut Admin") &&
        !frappe.user_roles.includes("System Manager"))) {
        console.log('yo')
        const removeButtons = () => {
            frm.remove_custom_button(__("Close"), __("Status"))
            frm.remove_custom_button(__("Purchase Receipt"), __("Create"))
            frm.remove_custom_button(__("Purchase Invoice"), __("Create"))
            frm.remove_custom_button(__("Payment"), __("Create"))
            frm.remove_custom_button(__("Payment Request"), __("Create"))
            frm.remove_custom_button(__("Create"))
            frm.remove_custom_button(__('Purchase Return'), __('Create'));
            frm.remove_custom_button(__('Make Stock Entry'), __('Create'));
            frm.remove_custom_button(__('Retention Stock Entry'), __('Create'));
            frm.remove_custom_button(__('Reopen'), __("Status"))
            frm.remove_custom_button(__('Update Items'))
        }


        setTimeout(removeButtons, 1000)
    }
    frm.get_field('custom_print').onclick = function () {
        var myImage = frm.doc.custom_qr_code_base;
        var image = new Image();
        image.src = myImage;
        var myWindow = window.open("", "Image");
        myWindow.document.body.appendChild(image)
        myWindow.print()
    }
    frm.get_field('custom_download').onclick = function () {
        var a = document.createElement("a");
        a.href = frm.doc.custom_qr_code_base;
        a.download = "Image.png";
        a.click();
        a.remove()
    }

}
frappe.ui.form.on('Purchase Order', {
    onload(frm) {
        createReceiptButton(frm)

        frappe.call({
            method: "edu_quality.overrides_hooks.purchase_order.generate_html_table",
            args: {
                self: frm.doc
            }, callback: function (r) {
                if (r.message) {
                    const challan_html = frm.get_field('custom_challan_detail');
                    var columns = generateColumns(r.message[1])
                    var data = r.message[2]

                    //     challan_html.df.options = `<div
                    //     style="
                    //       border-radius: var(--border-radius-md);
                    //       border: 1px solid var(--border-color);
                    //       box-shadow: none;
                    //       background-color: var(--card-bg);
                    //     "
                    //   >
                    //     <div style="font-weight: normal; background-color: var(--subtle-fg)"></div>
                    //   </div>
                    //   `

                    frm.fields_dict.custom_challan_detail.wrapper.innerHTML = `<div class="d-flex flex-column">${data.map((datum) => (
                        generateOrderCard(datum.item_code, datum.total_qty, datum.chapter, datum.subject)
                    ))}</div>

                `

                    // <div style="margin-top:6px;"><input type="checkbox"/></div>
                    // challan_html.set_options()
                    // const datatable = new DataTable(frm.fields_dict.custom_challan_detail.wrapper, { columns, data, checkboxColumn: true });
                    // console.log(datatable.rowmanager.getCheckedRows(), 'ha')
                    // challan_html.df.options = r.message[0]
                    // challan_html.set_options()
                }

            }
        })
    },
    refresh(frm) {
        removeBtnsForPrinters(frm)
        // your code here

    }
})
