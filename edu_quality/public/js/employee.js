frappe.ui.form.on('Employee', {
    refresh: function (frm) {
        if (frm.doc.status == "Active") {
            frm.add_custom_button(__('Mark Ex Employee'), function () {
                frappe.confirm(
                    'Are you sure you want to mark this employee as Left?',
                    () => {
                        frappe.call({
                            method: "edu_quality.edu_quality.server_scripts.employee.mark_ex_employee",
                            type: "POST",
                            args: {
                                employee: frm.doc.name
                            },
                            callback: function (response) {
                                frappe.show_alert({
                                    message: __(response.message),
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        });
                    },
                    () => {
                        frappe.show_alert({
                            message: __('Action Cancelled'),
                            indicator: 'orange'
                        });
                    }
                );
            });
        }
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
                                if (response.message.status == "error") {
                                    frappe.show_alert({
                                        message: __(response.message.message),
                                        indicator: 'red'
                                    });
                                }else {
                                    frappe.show_alert({
                                        message: __(response.message),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                }
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
