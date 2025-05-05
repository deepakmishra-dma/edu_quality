frappe.pages['scan-birthday-qr'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Scan QR for Birthday Photo',
		single_column: true
	});
	const el = page.wrapper.find('.container.page-body');
	// const el = document.querySelector('.container.page-body')
	const d = make_fieldgroup(el, [
		{
			label: 'Enter Student Ref no',
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