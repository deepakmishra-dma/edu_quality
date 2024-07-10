frappe.pages['scan-challan'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Scan Challans',
		single_column: true
	});
	const el = document.querySelector('.container.page-body')
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
				if (images?.data)
					frappe.call({
						method: "edu_quality.api.scan_receipts.find_url_to_redirect_to",
						args: {
							key: images?.data,
							type: "POST",
						}, callback: (r) => {
							if (r.message) {
								frappe.set_route(`/app${r.message}`)
							}
						}
					})
			}
		},
		{
			label: 'Submit',
			fieldname: 'submitbtn',
			fieldtype: 'Button',
			click: async () => {
				frappe.call({
					method: "edu_quality.api.scan_receipts.find_url_to_redirect_to",
					args: {
						key: d['fields_dict']['qr_code']['input'].value,
						type: "POST",
					}, callback: (r) => {
						if (r.message) {
							frappe.set_route(`/app${r.message}`)
						}
					}
				})

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