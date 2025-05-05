frappe.ui.form.on('Employee', {
    refresh: function (frm) {
        if (frm.doc.status == "Left" && frm.doc.is_migrated == 0) {
            frm.add_custom_button(__('Migrate Data'), function () {
                let d = new frappe.ui.Dialog({
                    title: 'Migrate Employee Data to Another Employee',
                    fields: [
                        {
                            label: 'Employee',
                            fieldname: 'employee',
                            fieldtype: 'Link',
                            options: "Employee",
                            get_query: function () {
                                return {
                                    doctype: 'Employee',
                                    filters: {
                                        status: "Active",
                                    },
                                };
                            }
                        }
                    ],
                    size: 'large',
                    primary_action_label: 'Submit',
                    primary_action(values) {
                        frappe.call({
                            method: "edu_quality.edu_quality.server_scripts.employee.migrate_employee_data",
                            type: "POST",
                            args: {
                                employee: frm.doc.name,
                                new_employee: values.employee
                            },
                            callback: function (response) {
                                frappe.show_alert({
                                    message: __(response.message),
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        });
                        d.hide();
                    }
                });

                d.show();

            });
        }
    }
});
