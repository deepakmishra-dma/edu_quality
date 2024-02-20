frappe.ui.form.on("Division Creation Tool", "get_courses", function(frm) {
	frm.set_value("courses",[]);
		frappe.call({
			method: "get_courses",
			doc:frm.doc,
			callback: function(r) {
				if(r.message) {
					console.log(r.message);
					frm.set_value("courses", r.message);
				}
			}
		})
});




frappe.ui.form.on("Division Creation Tool", "refresh", function(frm) {
	frm.disable_save();


	frm.page.set_primary_action(__("Create Student Groups"), function() {
		frappe.call({
			method: "create_student_groups",
			doc:frm.doc
		})
	});

	frappe.call({
		method: "get_current_academic_year",
		doc:frm.doc,
		callback: function(r) {
			if(r.message) {
				console.log(r.message);
				frm.set_value("academic_year", r.message);
			}
		}
	})
	
	frappe.call({
		method: "get_next_academic_year",
		doc:frm.doc,
		callback: function(r) {
			if(r.message) {
				console.log(r.message);
				frm.set_value("next_academic_year", r.message);
			}
		}
	})






	frappe.realtime.on("student_group_creation_progress", function(data) {
		if(data.progress) {
			frappe.hide_msgprint(true);
			frappe.show_progress(__("Creating student groups"), data.progress[0],data.progress[1]);
		}
	});
});



frappe.ui.form.on("Division Creation Tool", "onload", function(frm){
	cur_frm.set_query("academic_term",function(){
		return{
			"filters":{
				"academic_year": (frm.doc.academic_year)
			}
		};
	});
});
