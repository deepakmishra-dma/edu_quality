frappe.listview_settings['CBSE LOC'] = {
    refresh: function (listview) {
        listview.page.add_menu_item(__("Generate Confirmations"), function () {

            let d = new frappe.ui.Dialog({
                title: "Generate Confirmations",
                fields: [
                    {
                        fieldname: "program",
                        label: "Class",
                        fieldtype: "Link",
                        options: "Program"
                    },
                    {
                        fieldname: "status",
                        label: "Student Status",
                        fieldtype: "Select",
                        options: ["Current student", "Defaulter", "New student"],
                        default: "Current student"
                    }
                ],
                size: "small",
                primary_action_label: "Generate",
                primary_action(values) {
                    frappe.call({
                        method: "edu_quality.edu_quality.doctype.cbse_loc.cbse_loc.generate_confirmations",
                        type: "POST",
                        args: {
                            program: values.program,
                            status: values.status
                        },
                        callback: function (response) {
                            if (response.message.status == "1") {
                                frappe.show_alert({
                                    message: __("Enqueued for generation"),
                                    indicator: 'green'
                                });
                                d.hide();
                            }
                            else {
                                frappe.show_alert({
                                    message: __(response.message.error),
                                    indicator: 'red'
                                });
                            }
                        }
                    })
                }
            })
            d.show();
        });
    }

}