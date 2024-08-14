
// import DataTable from "frappe-datatable";

// window.DataTable = DataTable;
function printQR(qrCode) {
    var myImage = qrCode;
    var image = new Image();
    image.src = myImage;
    var myWindow = window.open("", "Image");
    myWindow.document.body.appendChild(image)
    myWindow.print()
}

function generateColumns(columns) {
    const generatedColumn = []

    columns.forEach((column) => {
        generatedColumn.push({
            ...column, format: (value, row, column, data) => { return value }
        })
    })
    return generatedColumn
}

async function getItemQR(item_code) {
    // const qrCodeBase64 = await frappe.db.get_value("Purchase Receipt",{"name":item_code},"custom_qr_code_base")
    // printQR(qrCodeBase64)


}


function generateOrderCard(itemCode, totalQty, chapter, subject, productURL, item_created) {


    return `<div
                  style="
                    border-radius: var(--border-radius-md);
                    border: 1px solid ${item_created ? "var(--alert-text-success)" : "var(--border-color)"};
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
                  <div style="margin-top:8px;margin-bottom:8px;display:flex; gap:12px;"><div><a href="${productURL}" target="__blank"><i class="fa fa-file" style="color:rgb(29 78 216);font-size:22px" aria-hidden="true" ></i></a></div>${item_created ? `<button data-is-print="true" data-item-code="${itemCode}" onclick=""><i style="color:rgb(29 78 216);font-size:22px" aria-hidden="true" class="fa fa-qrcode"  data-is-print="true" data-item-code="${itemCode}" aria-hidden="true"></i></button>` : ""}</div>
                  <div style="display:flex; align-items:center;gap:4px;" >
                <div style="margin-top:4px;">Printed</div><input data-item-code="${itemCode}" ${item_created ? "disabled" : ""} ${item_created ? `checked="${item_created}"` : ""}  type="checkbox" style="width:22px !important;height:22px;flex-shrink:0;margin-top:8px;" ></input></div> 
                  </div></div>
                </div>`
}
function getCheckedItems(frm) {
    const inputsList = Array.from(frm.fields_dict.custom_challan_detail.wrapper.querySelectorAll("input:not([disabled])[type='checkbox']"))
    return inputsList.filter((elem) => {
        return elem.checked
    }).map(elem => elem.dataset.itemCode)
}
function createReceiptButton(frm) {
    if ((frappe.user_roles.includes("Printer") || frappe.user_roles.includes("Administrator") || frappe.user_roles.includes("Walnut Admin") ||
        frappe.user_roles.includes("System_Manager")))
        frm.add_custom_button(__('Create Challans'), async function () {
            const checkedItems = getCheckedItems(frm)
            var d = new frappe.ui.Dialog({
                title: 'New Purchase Challans',
                fields: [
                    {
                        label: "This Will Create Challan for the following selected items across all schools.",
                        fieldname: 'challan_table',
                        fieldtype: 'HTML',

                        read_only: true
                    }],
                primary_action_label: 'Create',
                async primary_action(values) {
                    if (checkedItems)
                        frappe.call({
                            method: 'edu_quality.overrides_hooks.purchase_order.create_purchase_receipt_for_all_schools',
                            args: {
                                self: frm.doc,
                                selected_items: checkedItems
                            },
                            callback: (r) => {
                                if (r.message) {
                                    frappe.msgprint({
                                        indicator: "green",
                                        title: __("Created Successfully"),
                                        message: __(
                                            "Receipts Created for Selected Items For Each School Successfully"
                                        ),
                                    });
                                }
                            }
                        })



                },
            })
            setTimeout(() => {


                frappe.call({
                    method: "edu_quality.overrides_hooks.purchase_order.generate_challan_list",
                    args: {
                        self: frm.doc,
                        selected_items: checkedItems
                    }, callback: function (r) {
                        if (r.message) {
                            const challan_html = frm.get_field('custom_challan_detail');
                            console.log(r.message, 'sss')
                            var columns = generateColumns(r.message[1])
                            var data = r.message[2]
                            const datatable = new DataTable(d.fields_dict.challan_table.wrapper, { columns, data });

                        }

                    }
                })
            }, 1000)


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
        printQR(frm.doc.custom_qr_code_base)
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
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Send Test Mail'), () => {
                frappe.msgprint(
                    {
                        title: __('Notification'),
                        message: __('Are you sure you want to proceed, with sending the email to content creator group?'),
                        primary_action: {
                            'label': 'Proceed',
                            // either one of the actions can be passed
                            'server_action': 'edu_quality.overrides_hooks.purchase_order.send_test_order_email',
                            'args': { self: frm.doc }
                        }
                    })
            })
        }

        frappe.call({
            method: "edu_quality.overrides_hooks.purchase_order.generate_challan_list",
            args: {
                self: frm.doc,

            }, callback: function (r) {
                if (r.message) {
                    const challan_html = frm.get_field('custom_challan_detail');
                    var columns = generateColumns(r.message[1])

                    var data = r.message[2]

                    setTimeout(() => {
                        const el = document.createElement('div')
                        el.addEventListener('click', (e) => {
                            console.log('click', e.target)
                            const dataset = e.target.dataset
                            if (dataset.isPrint) {
                                frappe.call({
                                    method: "edu_quality.overrides_hooks.purchase_order.get_linked_receipts",
                                    args: {
                                        name: frm.doc.name,
                                        item_code: dataset.itemCode
                                    }, callback: function (r) {
                                        if (r.message) {
                                            console.log(r.message.length)
                                            if (r.message.length)
                                                frappe.msgprint({
                                                    title: __('Linked Receipts'),
                                                    indicator: 'green',
                                                    message: __(r.message?.map((el => {
                                                        return `<div><a href="/app/purchase-receipt/${el.parent}" data-name="${el.parent}" data-value="${el.parent}" onclick="event.stopPropagation();event.preventDefault();frappe.set_route('/app/purchase-receipt/${el.parent}')">${el.parent}</a></div>`
                                                    })).join(' '))
                                                })


                                        }

                                    }
                                })

                                getItemQR(e.target.dataset.itemCode)
                            }
                        })
                        el.classList.add(["d-flex", "flex-column"])
                        frm.fields_dict.custom_challan_detail.wrapper.innerHTML = ''
                        el.innerHTML = `${data.map((datum) => (
                            generateOrderCard(datum.item_code, datum.total_qty, datum.chapter, datum.subject, datum.product_url, datum.receipt_created)
                        ))}
                        
                    `
                        frm.fields_dict.custom_challan_detail.wrapper.appendChild(el)
                    }, 1000)

                }

            }
        })
    },
    refresh(frm) {
        removeBtnsForPrinters(frm)
        // your code here

    }
})
