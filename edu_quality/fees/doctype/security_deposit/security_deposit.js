// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Security Deposit', {
	school: function(frm) {
		frm.set_query("program", function() {
		return {
			 "filters": {
				 "school": frm.doc.school
				 }
			 };
		 });
	 }
});
