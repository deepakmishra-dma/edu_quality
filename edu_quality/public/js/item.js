async function getItemCode(frm) {
    hidePrintCheckBtn(frm)
    if (!frm.doc.custom_subject || !frm.doc.custom_class || !frm.doc.custom_textbook || !frm.doc.custom_chapter || !frm.doc.item_group || !frm.doc.custom_is_cmap) return
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
// function queryTextbook(frm) {
//     frm.set_query("custom_textbook", function () {
//         return {
//             filters: {
//                 "subject": frm.doc.custom_subject,
//                 "class": frm.doc.custom_class
//             }
//         }
//     })
// }
function uploadFileButton(frm) {

    frm.get_field('custom_upload_file_to_drive').onclick = async function () {
        if (frm.doc.__islocal) {
            frappe.msgprint({
                message: __("Please Save the item before uploading product document on drive"),
                indicator: "red",
                title: __("Error")
            });
            return
        }
        if (!frm.doc.custom_is_cmap) {
            frappe.msgprint({
                message: __("Can only upload file if item is of type cmap"),
                indicator: "red",
                title: __("Error getting worksheet header")
            });
            return
        }
        const item_group_doc = await frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Item Group",
                name: frm.doc.item_group,
            },

        });


        const allowed_extensions = item_group_doc?.message?.custom_allowed_file_extensions?.split(",")?.map((ext) => `${ext}`.toLowerCase()) || []
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = allowed_extensions?.map((ext) => `.${ext}`).join(",");

        input.onchange = function () {
            const file = input.files[0];
            if (file) {
                const ext = file.name.split('.').pop().toLowerCase();
                if (allowed_extensions.includes(ext)) {
                    const form_data = new FormData();
                    form_data.append('file', file);
                    form_data.append('doctype', frm.doctype);
                    form_data.append('docname', frm.docname);
                    form_data.append('file_fieldname', 'attach_files'); // Change this to your file fieldname
                    form_data.append('files', input.files)
                    // Send the FormData object to the server
                    fetch('/api/method/edu_quality.overrides_hooks.item.upload_to_drive', {
                        method: 'POST',
                        body: form_data
                    }).then(response => {
                        if (response.ok) {
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to upload file.'));
                        }
                    }).catch(error => {
                        frappe.msgprint(__('An error occurred while uploading file.'));
                        console.error('Error:', error);
                    });
                } else {
                    frappe.msgprint(__(`Please upload only ${allowed_extensions?.map((ext) => `.${ext}`).join(",")} files.`));
                }
            }
        };
        input.click();
    }


}
function queryTopic(frm) {
    frm.set_query("custom_chapter", function () {
        return {
            filters: {
                // "custom_subject": frm.doc.custom_subject,
                // "custom_class": frm.doc.custom_class,
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

async function getLinkedSubject(frm) {
    if (frm.doc.custom_class)
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Class Type",
                name: frm.doc.custom_class,
            },
            callback(r) {
                if (r.message) {
                    const classData = r.message;

                    const arrayOfSubjects = classData.subject.map(function (obj) {
                        return obj.subject;
                    });
                    frm.set_query("custom_subject", function () {
                        return {
                            filters: [['name', 'in', arrayOfSubjects]]
                        }
                    })
                }
            }
        });



}

function appendUrl(frm) {
    $(frm.fields_dict.custom_product_url.$wrapper).find('label').html(`<a target="__blank" href="${frm.doc.custom_product_url}">Product URL <i class="fa fa-external-link" aria-hidden="true"></i></a>`)


}
frappe.ui.form.on("Item", {
    refresh: function (frm) {



        appendUrl(frm)
        uploadFileButton(frm)
        getLinkedSubject(frm)
        hidePrintCheckBtn(frm)
        // queryTextbook(frm)
        queryTopic(frm)

        if (!frm.doc.__islocal) {
            frm.disable_save()
            frm.page.set_primary_action(__('Save'), () => customSaveHandler(frm));
            frappe.call({
                method: "edu_quality.overrides_hooks.item.get_qr_code",
                args: {
                    name: frm.doc.name
                }, callback: function (r) {
                    frm.fields_dict.custom_qr_code_preview.wrapper.innerHTML = `<img src="${r.message}"/>
            `
                }
            })
        }

        frm.get_field('custom_view_worksheet_header').onclick = function () {
            if (frm.doc.__islocal) {
                frappe.msgprint({
                    message: __("Please Save the item before accessing the worksheet header"),
                    indicator: "red",
                    title: __("Error getting worksheet header")
                });
                return
            }
            if (!frm.doc.custom_is_cmap) {
                frappe.msgprint({
                    message: __("Can only see worksheet Header if item is of type cmap"),
                    indicator: "red",
                    title: __("Error getting worksheet header")
                });
                return
            }
            if (!frm.doc.__islocal) {
                window.open(`/api/method/edu_quality.overrides_hooks.item.get_worksheet_template?name=${frm.doc.name}`)
            }
        }
    },
    onload: function (frm) {
        appendUrl(frm)
        if (frm.doc__islocal) {
            frm.set_value('custom_sheet_number', 0);
        }
        if (frm.doc.__islocal) {
            frm.set_value('custom_product_url', '')
            frm.set_value('custom_product_folder', '')
            frm.set_value('custom_class_subject_folder', '')
        }
        if (!frm.doc.custom_is_cmap) {
            NotCmapFilter(frm);
        }
        else if (frm.doc.custom_is_cmap === 1) {
            frm.set_query("item_group", function () {
                return {
                    "filters": {
                        "parent_item_group": "CMAP",

                    }
                }
            })
        }
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
    custom_chapter: getItemCode,
    custom_class: getLinkedSubject,
    custom_textbook: getClassSubject
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
function hidePrintCheckBtn(frm) {
    if (!frm.doc.item_group) return false
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Item Group",
            name: frm.doc.item_group
        },
        callback: function (response) {
            var doc = response.message;
            if (doc.custom_printable == 0) {
                $(frm.fields_dict.custom_print_ready.$wrapper).css("display", "none")
            }
            else {
                $(frm.fields_dict.custom_print_ready.$wrapper).css("display", "inline-block")
            }



        }
    });
}
function getClassSubject(frm) {
    if (!frm.doc.custom_textbook) return
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Textbook",
            name: frm.doc.custom_textbook
        },
        callback: function (response) {
            var doc = response.message;
            frm.set_value('custom_class', doc.class)
            frm.set_value('custom_subject', doc.subject)


        }
    });


}

function customSaveHandler(frm) {

    // Your custom logic here
    // For example, you can display a message
    let d = new frappe.ui.Dialog({
        title: 'Reason',
        fields: [
            {
                label: 'Reason for Change(min 10 characters)',
                fieldname: 'comment',
                fieldtype: 'Text',
                onchange: (event) => {
                    if (event.target.value.length >= 10) {
                        d.$wrapper.find(".btn-primary").prop('disabled', false)
                    }
                    else {
                        d.$wrapper.find(".btn-primary").prop('disabled', true)
                    }
                }
            },

        ],
        size: 'small', // small, large, extra-large 
        primary_action_label: 'Comment and Save',
        async primary_action(values) {
            if (!values.comment) return

            await frappe.call({
                "method": "frappe.desk.form.utils.add_comment",
                "args": {
                    reference_doctype: frm.doctype,
                    reference_name: frm.docname,
                    content: values.comment,
                    comment_email: frappe.session.user,
                    comment_by: frappe.session.user_fullname,
                }
            });
            d.hide();
            frm.save("Save")

        }
    });
    d.$wrapper.find(".btn-primary").prop('disabled', true)
    d.show();
}
