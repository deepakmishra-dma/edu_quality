// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('MGR Enrollment Log', {
	refresh: function(frm) {
		if(!frm.is_new()&frm.doc.enrollment__status!="Success")
		frm.add_custom_button(__('Enroll'), function () {
			frappe.call({
				method: "edu_quality.fees.doctype.mgr_enrollment_log.mgr_enrollment_log.re_enroll_student",
				type: "POST",
				args: {
					id: frm.doc.name,
				},
				callback: function (response) {
					frappe.show_alert({
						message: __("Enroll Started"),
						indicator: 'green'
					});
				}
			})

			dialog.show();
		});

	}
});
