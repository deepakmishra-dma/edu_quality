// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
function handleCreatePurchaseOrder(frm) {
	let message = `
				<div>
					
					<p>Are you sure you want to create a Purchase Order, for the given ID cards ?</p>
				</div>`;

	frappe.confirm(__(message), () => {

		frappe.call({
			"method": "edu_quality.fees.doctype.permanent_id_card.permanent_id_card.create_purchase_order",

			"args": {
				name: frm.doc.name
			},
			callback: function (r) {
				if (r.message) {
					frappe.set_route(`/app/purchase-order/${r?.message?.name}`)
				}
			}
		})


	})
}
frappe.ui.form.on('Permanent Id Card', {
	refresh: function (frm) {
		frm.add_custom_button(__("Create Purchase Order"), () => handleCreatePurchaseOrder(frm))
	}
});
