frappe.listview_settings['Student'] = {
    hide_name_column: true,
    button: {
        show(doc) {
            return doc.student_mobile_number;
        },
        get_label() {
            return '<img src="https://static.vecteezy.com/system/resources/thumbnails/000/423/339/small/Multimedia__2850_29.jpg" width="14",height="14">';
        },
        get_description(doc) {
            return __('Copy {0}', [`${doc.student_mobile_number}`])
        },
        action(doc) {
            var tempTextarea = document.createElement('textarea');
            tempTextarea.value = doc.student_mobile_number;
            document.body.appendChild(tempTextarea);
            tempTextarea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextarea);
        }
    },

    refresh: function (listview) {
        listview.page.add_menu_item(__("Import Student"), function () {
            let d = new frappe.ui.Dialog({
                title: 'Import Students',
                fields: [
                    {
                        label: 'School',
                        fieldname: 'school',
                        fieldtype: 'Link',
                        options: "School",
                        reqd: true
                    },
                    {
                        label: 'Academic Year',
                        fieldname: 'academic_year',
                        fieldtype: 'Link',
                        options: "Academic Year",
                        reqd: true
                    },
                    {
                        label: 'Class',
                        fieldname: 'program',
                        fieldtype: 'Link',
                        options: "Program",
                        reqd: true
                    },
                    {
                        label: 'Division',
                        fieldname: 'division',
                        fieldtype: 'Link',
                        options: "Student Group",
                        reqd: true
                    }
                ],
                size: 'large',
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        method: "edu_quality.public.py.student.import_student",
                        type: "POST",
                        args: {
                            school: values.school,
                            program: values.program,
                            division: values.division,
                            academic_year: values.academic_year
                        },
                        callback: function (response) {
                            console.log(response);
                            if (response.message.status == 'success') {
                                frappe.show_alert({
                                    message: __(response.message.res),
                                    indicator: 'green'
                                });
                            }
                        }
                    });
                    d.hide();
                }
            });

            d.show();
            frappe.set_route("List", "Student");
        });
    }
}