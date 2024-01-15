// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('MGR MigratorTool', {
	refresh: function(frm) {
		addProgressButton(frm);
	},
	import_student:frm => {
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
	},
  import_fees:frm => {
		frappe.confirm('Are you sure you want to proceed?',
                () => {
                    frappe.call({
                        method: "edu_quality.fees.mgr_fees.fee_advance",
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
	}
});

function addProgressButton(frm) {
    function showProgress() { 
      frappe.call({
        method: 'edu_quality.public.py.student.get_migration_progress',
        freeze: true,
        callback: res => {
            frm.set_intro('');
          if (res.message.progress) {
            const color = res.message?.progress?.includes('100')
              ? 'green'
              : 'orange';
            let message = res.message.job ? `${res.message.job}: ` : '';
            message += res.message.progress;
			frm.set_intro("Databases:("+res.message.db+'/3)')
            frm.set_intro(message, color);
          } else {
            frm.set_intro('No Migration Jobs running', 'blue');
          }
        },
      });
    }
  
    showProgress();
    
    frm.add_custom_button('Get Progress', () => {
      showProgress();
    });
  }