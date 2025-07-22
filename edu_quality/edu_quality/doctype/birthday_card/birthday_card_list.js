// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
let pdfUrl;
frappe.listview_settings["Birthday Card"] = {
    refresh: function (listview) {
        listview.page.add_inner_button(__("Print Birthday Cards"), async function () {
            const dialog = new frappe.ui.Dialog({
                title: __('Print Todays Birthday Cards'),
                fields: [
                    {
                        fieldtype: 'Date',
                        label: __('From Date'),
                        fieldname: 'from_date',
                        default: frappe.datetime.nowdate()
                    },
                    {fieldtype: 'Column Break'},
                    {
                        fieldtype: 'Date',
                        label: __('To Date'),
                        fieldname: 'to_date',
                        default: frappe.datetime.nowdate()
                    },
                ],
                primary_action_label: __('Submit'),
                primary_action: async function (values) {
                    const headers = new Headers();
                    headers.append('X-Frappe-CSRF-Token', frappe.csrf_token);
                    headers.append('Content-Type', 'application/json');
                    const payload = { "from_date": values.from_date, "to_date": values.to_date }

                    try {
                        const response = await fetch(`/api/method/edu_quality.edu_quality.doctype.birthday_card.birthday_card.print_todays_birthday_card`, {
                            method: 'POST',
                            headers: headers,
                            body: JSON.stringify(payload)
                        });

                        const file = await response.blob();
                        await handleFileResponse(file, values);
                    } catch (e) {
                        console.error("An error occurred while trying to print today's birthday cards:", e);
                    } finally {
                        if (pdfUrl) {
                            URL.revokeObjectURL(pdfUrl);
                        }
                    }
                    dialog.hide();
                }
            });

            dialog.show();
        }).addClass('btn-primary');
    }
}

// Function to handle file response
async function handleFileResponse(file, values) {
    try {
        const from_date = new Date(values.from_date);
        const fromMonthName = from_date.toLocaleString('default', { month: 'long' });
        const from_day = from_date.getDate();
        const to_date = new Date(values.to_date);
        const toMonthName = to_date.toLocaleString('default', { month: 'long' });
        const to_day = to_date.getDate();

        const text = await file.text();
        const { message } = JSON.parse(text);
        if (message === false) {
            showMessageDialog(`No Birthday Card Found for birthdates between ${fromMonthName} ${from_day} and ${toMonthName} ${to_day}`);
            return;
        }
    } catch (e) {
        console.info("PDF generated successfully!");
    }

    showMessageDialog("Birthday Cards PDF Generated Successfully", file);
}

// Function to show message dialog
function showMessageDialog(message, file = null) {
    frappe.msgprint({
        title: __("Birthday Cards PDF Generated!"),
        message: __(message),
        primary_action: {
            label: file ? __("Open PDF") : __("OK"),
            action: function () {
                if (file) {
                    pdfUrl = URL.createObjectURL(file);
                    window.open(pdfUrl, '_blank');
                }
                frappe.hide_msgprint();
            }
        }
    });
}