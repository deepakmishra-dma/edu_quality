// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fee Advance', {
	refresh: function (frm) {
		if (frm.doc.docstatus > 0) {
			frm.add_custom_button(__('Accounting Ledger'), function () {
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
			frm.add_custom_button(__("Payment Entry"), function () {
				frappe.set_route("List", "Payment Entry", { "reference_name": frm.doc.name });
			}, __("View"));
			frm.add_custom_button(__("Payment Request"), function () {
				frappe.set_route("List", "Payment Request", { "Payment Request Reference.reference_name": frm.doc.name });
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
			
			const table_fields = [
				{ fieldname: "company", fieldtype: "Link", in_list_view: 1, label: "Company", options: "Company", reqd: 1 },
				{ fieldname: "amount", fieldtype: "Currency", in_list_view: 1, label: "Amount", reqd: 1 },
				{ fieldname: "reference_number", fieldtype: "Data", in_list_view: 1, label: "Reference Number", reqd: 1 }
			];

			let check = false;
			let html_content = ``;
			let pdf_url = '';
			let is_rules_and_re = 0;
			let hide_check_reg = 1;


			frm.add_custom_button("Manual Collection", function () {
				let d = new frappe.ui.Dialog({
					title: 'Manual Collection',
					fields: [
						{ label: 'Payment Term', fieldname: 'payment_term', fieldtype: 'Select', options: frm.doc.payment_term, onchange: onPaymentTermChange },
						{ label: 'Payment Mode', fieldname: 'payment_mode', fieldtype: 'Link', options: "Mode of Payment" },
						{ fieldtype: "Table", fieldname: "table", label: "Cheque/ DD Details", cannot_add_rows: true, in_place_edit: true, reqd: 1, data: [], fields: table_fields },
						{ fieldtype: "Check", fieldname: "undertaking_check", label: `Accept Undertaking Before Making Payment <a href="${pdf_url}">Click here</a>`, hidden: hide_check_reg, reqd: is_rules_and_re, default: check, read_only: check, onchange: onUndertakingCheckChange },
						{ fieldtype: "HTML", fieldname: "undertaking_content", label: "", options: html_content }
					],
					size: 'large',
					primary_action_label: 'Submit',
					primary_action: onDialogSubmit
				});

				if (!check && !hide_check_reg) {
					d.fields_dict.undertaking_check.input.onclick = function () {
						if (d.fields_dict.undertaking_check.input.checked) {
							sendOtp(frm);
						}
					};
				}

				d.show();

				if (!hide_check_reg) {
					setTimeout(() => {
						console.log("Delayed for 1 second.");
						console.log(document.querySelector(".btn-modal-primary"));
						const x = document.querySelector(".btn-modal-primary");
						x.style.display = 'none';
					}, 1000);
				}
			});

			function onPaymentTermChange(e) {
				frappe.call({
					method: "edu_quality.edu_quality.server_scripts.manual_payment.get_payment_details",
					type: "POST",
					args: { fee: frm.doc.name, doctype:frm.doc.doctype, term: frm.doc.payment_term },
					callback: function (response) {
						console.log(response.message);
						d.set_df_property('table', 'data', response.message);
					}
				});
			}

			function onUndertakingCheckChange(e) {
				if (e.value) {
					d.set_df_property(
						'undertaking_content',
						'options',
						`<script>... </script><div class="form-inline m-1" id="otp-area">...</div>`
					);
				}
			}

			function onDialogSubmit(values) {
				if (!values.undertaking_check && !hide_check_reg) {
					frappe.throw("Please select Terms and conditions");
				} else {
					frappe.call({
						method: "edu_quality.edu_quality.server_scripts.manual_payment.manual_payment",
						type: "POST",
						args: { term: values.payment_term, fee: frm.doc.name, data: values.table, payment_mode: values.payment_mode },
						callback: function (response) {
							showAlert(response.message, 'green');
							frm.reload_doc();
						}
					});
					d.hide();
				}
			}
		}
	}
});