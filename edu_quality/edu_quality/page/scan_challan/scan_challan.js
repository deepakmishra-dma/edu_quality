frappe.pages['scan-challan'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Scan Challans',
		single_column: true
	});
	const el = page.wrapper.find('.container.page-body');
	// const el = document.querySelector('.container.page-body')
	const d = make_fieldgroup(el, [
		{
			label: 'Enter Purchase Order/ Challan No',
			fieldname: 'qr_code',
			fieldtype: 'Data',
		},
		{
			label: '<i class="fa fa-qrcode" aria-hidden="true"></i> Open Scanner',
			fieldname: 'scanbtn',
			fieldtype: 'Button',
			click: async () => {
				const images = await nativeInterface.execute('openWebViewScanner')
				d.set_value('qr_code', images?.data)
				if (images?.data) {
					postScanQr(images?.data)

				}
			}
		},
		{
			label: 'Submit',
			fieldname: 'submitbtn',
			fieldtype: 'Button',
			click: async () => {
				const qr_code = d['fields_dict']['qr_code']['input'].value
				if (qr_code)
					postScanQr(qr_code)

			}
		},


	])
}

function make_fieldgroup(parent, ddf_list) {
	fg = new frappe.ui.FieldGroup({
		"fields": ddf_list,
		"parent": parent
	});
	fg.make();
	console.log(fg)
	return fg

}

function postScanQr(key) {
	let d = new frappe.ui.Dialog({
		title: 'Confirm?',

		primary_action_label: __("हो (Yes)"),
		primary_action: () => {
			frappe.call({
				method: "edu_quality.api.scan_receipts.find_url_to_redirect_to",
				args: {
					key: key,
					type: "POST",
				}, callback: (r) => {
					console.log(r.message)
					if ((frappe.user_roles.includes("Watchman") && !frappe.user_roles.includes("Administrator") && !frappe.user_roles.includes("School Admin") && !frappe.user_roles.includes("System Manager") && r.message)) {

						frappe.msgprint({
							indicator: "green",
							title: __("Updated Successfully"),
							message: __(
								`Receipt ${key} marked as received`
							),
						});
						return d.set_value('qr_code', '')
					}
					if (r.message && typeof r.message === "string") {
						frappe.set_route(`/app${r.message}`)
					}
				}
			})
			d.hide();
		},
		secondary_action_label: __("नाही (No)"),
		secondary_action: () => {
			d.hide();
		},
	});
	d.show();
	d.set_message("Are you sure? नक्की ना?");

}