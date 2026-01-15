frappe.listview_settings['Descriptive Question'] = {
    onload: function (listview) {
        listview.page.add_menu_item(__('Import CSV'), function () {
            var dialog = new frappe.ui.Dialog({
                title: __('Upload CSV File'),
                fields: [
                    {
                        fieldname: 'file',
                        label: __('CSV File'),
                        fieldtype: 'Attach',
                        reqd: 1
                    }
                ],
                primary_action_label: __('Import'),
                primary_action: function () {
                    var file = dialog.get_value('file');
                    if (file) {
                        let res = checkFilePermission(file);
                        if (res != false) {
                            dialog.hide();
                        }

                    } else {
                        frappe.msgprint(__('Please select a file.'));
                    }
                }
            });
            dialog.show();
        });


    }
};



function checkFilePermission(file) {
    frappe.call({
        method: 'edu_quality.edu_quality.doctype.ptm_scheduler.ptm_scheduler.check_file_permission',
        args: { 'file_url': file },
        callback: function (response) {
            if (response.message.status === 'success') {
                importCSVData(file);
            } else {
                frappe.msgprint(__('Only public files are allowed for upload.'));

            }
        }
    });
}

function importCSVData(file) {
    frappe.call({
        method: 'edu_quality.edu_quality.doctype.descriptive_question.descriptive_question.import_descriptive_ques',
        args: { 'url': file },
        callback: function (response) {
            if (response.message.status === 'success') {
                // Display success message with green indicator
                frappe.msgprint('<div style="color: green;">Success: ' + response.message.message + '</div>');
            } else {
                // Display failure message with red indicator
                frappe.msgprint('<div style="color: red;">Import failed: <br>' + response.message.message + '</div>');
            }
        },
        error: function (xhr, textStatus, error) {
            // Handle error in making the AJAX call
            frappe.msgprint('<div style="color: red;">Error occurred while importing data: <br>' + error + '</div>');
        }
    });
}


const uncheck = () => {
    var checkbox = document.querySelector('.level-item.list-check-all');

    // Check if the checkbox element exists
    if (checkbox) {
        // Simulate a click on the checkbox
        checkbox.click();
    } else {
        console.log('Checkbox element not found');
    }
}