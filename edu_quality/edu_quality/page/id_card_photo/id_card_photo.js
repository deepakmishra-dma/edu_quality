frappe.pages['id-card-photo'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'ID Card Photo',
		single_column: true
	});
	setTimeout(() => {
		const el = document.querySelector('.container.page-body')

		const d = make_fieldgroup(el, [
			{
				label: 'Enter Ref No',
				fieldname: 'ref_no',
				fieldtype: 'Data',
			},
			{
				label: '<i class="fa fa-qrcode" aria-hidden="true"></i> Open Scanner',
				fieldname: 'scanbtn',
				fieldtype: 'Button',
				click: async () => {
					const images = await nativeInterface.execute('openWebViewScanner')


					const [academicYear, school, refNo] = images?.data?.split("/")
					// frappe.msgprint(academicYear, school, refNo)
					d.set_value("ref_no", refNo || images?.data)
					// d.set_value('ref_no', images?.data)
				}
			},
			{
				label: 'Take Photo',
				fieldname: 'submitbtn',
				fieldtype: 'Button',
				click: async () => {
					const ref_no = d['fields_dict']['ref_no']['input'].value
					if (!ref_no) {
						frappe.msgprint("Enter Ref no or Scan QR")
					}
					const images = await nativeInterface.execute('openWebViewCamera', {
						multiple: true,

						preferredCameraType: 'rear',
						galleryTitle: "ID Card",
						saveInMedia: true,
						saveInFileName: ref_no,

					})
					if (images.length || !images) {
						d.set_value('ref_no', '')
					}
				}
			},


		])
	}, 2000);
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