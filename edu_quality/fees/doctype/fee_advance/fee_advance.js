// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fee Advance', {
	refresh: function(frm) {
        if(frm.doc.docstatus > 0) {
			frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: moment(frm.doc.modified).format('YYYY-MM-DD'),
					company: frm.doc.company,
					group_by: '',
					show_cancelled_entries: frm.doc.docstatus === 2
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
			frm.add_custom_button(__("Payment Entry"), function() {
				frappe.set_route("List", "Payment Entry", {"reference_name": frm.doc.name});
			}, __("View"));
            frm.add_custom_button(__("Payment Request"), function() {
				frappe.set_route("List", "Payment Request", {"Payment Request Reference.reference_name": frm.doc.name});
			}, __("View"));
			frm.add_custom_button(__('Modify Payment Plan'), function () {
				const doc = frm.doc;
				const dialog = new frappe.ui.Dialog({
					title: 'Modify Payment Plan',
					fields: [
						{
							label: 'Payment Plan',
							fieldname: 'payment_plan',
							fieldtype: 'Link',
							options: "Payment Plan",
							get_query: function () {
								return {
									doctype: 'Payment Plan',
									filters: {
										fee_structure: doc.fee_structure,
										name: ["!=", doc.payment_plan]
									},
								};
							}
						}
					],
					size: 'large',
					primary_action_label: 'Submit',
					primary_action: async function (values) {
						doc.payment_plan = values.payment_plan;
						await frappe.call({
							method: "edu_quality.edu_quality.server_scripts.payment_plan.change_payment_plan",
							type: "POST",
							args: {
								payment_plan: values.payment_plan,
								doctype: doc.doctype,
								fee_name: doc.name
							},
							callback: function (response) {
								frappe.show_alert({
									message: __(response.message),
									indicator: 'green'
								});
							},
							async: false
						});
						dialog.hide();
						frm.reload_doc();
					}
				});
				dialog.show();
			});
			frm.add_custom_button(__('Add Discount'), function () {
				let d = new frappe.ui.Dialog({
					title: 'Add Discount',
					fields: [
						{
							label: 'Discount Name',
							fieldname: 'discount_name',
							fieldtype: 'Link',
							options: "Discount Configuration",
							get_query: function () {
								return {
									doctype: 'Discount Configuration',
									filters: {
										fee_structure: frm.doc.fee_structure,
										type: "One Time"
									},
								};
							}
						}
					],
					size: 'large',
					primary_action_label: 'Submit',
					primary_action(values) {
						frappe.call({
							method: "edu_quality.public.py.discount.add_discount",
							type: "POST",
							args: {
								discount: values.discount_name,
								doctype: frm.doc.doctype,
								fee_name: frm.doc.name
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
	
			}, __("Discount"));
			frm.add_custom_button(__('Remove Discount'), function () {
				let d = new frappe.ui.Dialog({
					title: 'Remove Discount',
					fields: [
						{
							label: 'Discount Name',
							fieldname: 'discount_name',
							fieldtype: 'Link',
							options: "Discount Configuration",
							get_query: function () {
								return {
									doctype: 'Discount Configuration',
									filters: {
										fee_structure: frm.doc.fee_structure,
										type: "One Time"
									},
								};
							}
						}
					],
					size: 'large',
					primary_action_label: 'Submit',
					primary_action(values) {
						frappe.call({
							method: "edu_quality.public.py.discount.remove_discount",
							type: "POST",
							args: {
								discount: values.discount_name,
								doctype: frm.doc.doctype,
								fee_name: frm.doc.name
							},
							callback: function (response) {
								frappe.show_alert({
									message: __(response.message),
									indicator: 'orange'
								});
								frm.reload_doc();
							}
						});
						d.hide();
					}
				});
	
				d.show();
			}, __("Discount"));
		}
	}
});