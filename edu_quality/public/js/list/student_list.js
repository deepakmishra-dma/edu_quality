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
            frappe.confirm('Are you sure you want to proceed?',
                () => {
                    frappe.call({
                        method: "edu_quality.public.py.student.import_student",
                        type: "POST",
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
                }, () => {
                    frappe.show_alert({
                        message: __('Import Student cancelled.'),
                        indicator: 'orange'
                    });
                });
        });

        listview.page.add_menu_item(__('Create Fee Advance'), function () {
            let students = listview.get_checked_items();
            if (students.length > 0) {
                frappe.confirm('Are you sure you want to proceed?',
                    () => {
                        frappe.call({
                            method: "edu_quality.fees.doctype.fee_advance.fee_advance.fee_advance",
                            type: "POST",
                            args: {
                                students: students
                            },
                            callback: function (response) {
                                frappe.show_alert({
                                    message: __('Fee Advance Creation Scheduled Successfully'),
                                    indicator: 'green'
                                });
                            }
                        });
                    }, () => {
                        frappe.show_alert({
                            message: __('Action Cancelled'),
                            indicator: 'orange'
                        });
                    })
            } else {
                frappe.show_alert({
                    message: __('Please select at least one Students.'),
                    indicator: 'orange'
                });
            }
        }
        );

        
        addProgressButton(listview);


    }
    
};
function addProgressButton(listview) {
    function showProgress() {
      frappe.call({
        method: 'edu_quality.public.py.student.get_migration_progress',
        freeze: true,
        callback: res => {
            // listview.set_intro('');
          if (res.message.progress) {
            const color = res.message?.progress?.includes('100')
              ? 'green'
              : 'orange';
            let message = res.message.job ? `${res.message.job}: ` : '';
            message += res.message.progress;
            frappe.msgprint(message)
            listview.set_intro(message, color);
          } else {
            // listview.set_intro('No Migration Jobs running', 'blue');
          }
        },
      });
    }
  
    showProgress();
    
    // listview.add_custom_button('Get Progress', () => {
    //   showProgress();
    // });
  }