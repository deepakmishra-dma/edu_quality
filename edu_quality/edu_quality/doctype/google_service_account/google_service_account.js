// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Google Service Account', {
	// refresh: function(frm) {

	// }
	onload: function (frm) {
		return frappe.call({
			method: "edu_quality.edu_quality.doctype.google_service_account.google_service_account.get_folder_list",
			callback: function (r) {

				frm.set_df_property('root_folder', 'options', r.message)
				frm.set_df_property('class_photo_folder', 'options', r.message)
				frm.set_df_property('products_folder', 'options', r.message)
				frm.set_df_property('final_product_folder', 'options', r.message)
			}
		})
	}
});
