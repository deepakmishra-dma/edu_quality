frappe.listview_settings['PTM Scheduler'] = {
    onload:function(listview) {
        listview.page.add_menu_item(__('Import CSV'), function() {
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
                primary_action: function() {
                    var file = dialog.get_value('file');
                    if (file) {
                        let res = checkFilePermission(file);
                        if (res != false){
                            dialog.hide();
                        }
                        
                    } else {
                        frappe.msgprint(__('Please select a file.'));
                    }
                }
            });
            dialog.show();
        });

        listview.page.add_action_item(__('<i class="fa fa-video-camera"></i> Generate Gmeet Link'), function() {
            var selected_items = listview.get_checked_items();
            if (selected_items && selected_items.length > 0) {
                // Open a prompt/modal to gather meeting details
                frappe.db.get_list('User', {
                    filters: {'enabled': 1},
                    fields: ['name']
                }).then(function(response) {
                    if (response && response.length > 0) {
                        var enabledUsers = response.map(function(user) {
                            return user.name;
                        });
                        // Open a prompt/modal to gather meeting details
                        frappe.prompt([
                            {'fieldname': 'summary', 'fieldtype': 'Data', 'label': 'Meeting Summary', 'reqd': 1},
                            {'fieldname': 'regenerate', 'fieldtype': 'Check', 'label': 'Re-Generate (if Present Gmeet Link)'},
                            {'fieldname': 'imporsonate_user', 'fieldtype': 'Link', 'label': 'Select Gmeet Owner', 'options': 'User', 'reqd': 1}
                        ], function(values) {
                            // Handle button click action here
                            // values.summary contains the meeting summary
                            // values.date contains the date
                            // values.attendees_list contains the selected attendees
                            var items = selected_items.map(function(item) {
                                return item.name;
                            });
                            generate_gmeet_links(items, values.summary, values.imporsonate_user,values.regenerate);
                        }, 'Enter Details for Gmeet Link', 'Generate');
                    } else {
                        frappe.msgprint('No enabled users found!');
                    }
                });
                
            } else {
                frappe.msgprint('No items selected!');
            }
        });
    }
};



function checkFilePermission(file) {
    frappe.call({
        method: 'edu_quality.edu_quality.doctype.ptm_scheduler.ptm_scheduler.check_file_permission',
        args: { 'file_url': file },
        callback: function(response) {
            if (response.message.status === 'success') {
                importCSVData(file);
            } else {
                frappe.msgprint(__('Only public files are allowed for upload.'));
               
            }
        }
    });
}

// function importCSVData(file) {
//     frappe.call({
//         method: 'edu_quality.edu_quality.doctype.ptm_scheduler.ptm_scheduler.import_ptm_schedule_from_url',
//         args: { 'url': file },
//         callback: function (response) {
//             if (response.message.status === 'success') {
//                 frappe.msgprint(response.message.message);
//             } else {
//                 frappe.msgprint('Import failed: \n' + response.message.message);
//             }
//         }
//     });
// }
function importCSVData(file) {
    frappe.call({
        method: 'edu_quality.edu_quality.doctype.ptm_scheduler.ptm_scheduler.import_ptm_schedule_from_url',
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



function generate_gmeet_links(items,summary,imporsonate_user,regenerate) {
    frappe.dom.freeze(__(`Generating Gmeet Links...`));
    frappe.call({
        method: 'edu_quality.edu_quality.doctype.ptm_scheduler.ptm_scheduler.generate_meeting_function',
        args:{
            items,
            summary,
            imporsonate_user,
            regenerate,
            
        },
        callback: function (response) {
            frappe.dom.unfreeze()
            uncheck()
            if (response.message.status === 'success') {
                frappe.msgprint(response.message.message);
            } else {
                frappe.msgprint('Import failed: ' + response.message.message);
            }
        }
    });
}

const uncheck =() =>{
    var checkbox = document.querySelector('.level-item.list-check-all');

    // Check if the checkbox element exists
    if (checkbox) {
        // Simulate a click on the checkbox
        checkbox.click();
    } else {
        console.log('Checkbox element not found');
    }
}