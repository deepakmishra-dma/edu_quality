// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fee Advance', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && !frm.doc.fee_creation_status || frm.doc.fee_creation_status === 'Failed') {
			frm.add_custom_button(__('Create Fees'), function() {
				frappe.call({
					method: 'create_fees',
					doc: frm.doc,
					callback: function() {
						frm.refresh();
					}
				});
			}).addClass('btn-primary');
		}
		if (frm.doc.fee_creation_status === 'Successful') {
			frm.add_custom_button(__('View Fees Records'), function() {
				frappe.route_options = {
					fee_schedule: frm.doc.name
				};
				frappe.set_route('List', 'Fees');
			});
		}
	}
});

frappe.ui.form.on('Fee Schedule Student Group', {
	student_group: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.student_group && frm.doc.academic_year) {
			frappe.call({
				method: 'education.education.doctype.fee_schedule.fee_schedule.get_total_students',
				args: {
					'student_group': row.student_group,
					'academic_year': frm.doc.academic_year
				},
				callback: function(r) {
					if (!r.exc) {
						frappe.model.set_value(cdt, cdn, 'total_students', r.message);
					}
				}
			});
		}
	}
})