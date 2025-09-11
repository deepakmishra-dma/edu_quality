var globalPage
frappe.pages['process-exam-result'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Process Exam Result',
		single_column: true
	});
	globalPage = page
	onLoad()
}

function onLoad() {
	const el = globalPage.wrapper.find('.container.page-body');

	make_fieldgroup(el, [
		{
			label: 'Academic Year',
			fieldname: 'acad_year',
			fieldtype: 'Link',
			reqd: 1
		},
		{
			label: "School",
			fieldname: "school",
			fieldtype: "Link",
			options: "School",
			reqd: 1
		},
		{
			label: "Exam Name",
			fieldname: "exam_name",
			fieldtype: "Link",
			options: "Assessment Group",
			reqd: 1
		},
		{
			label: "Class",
			fieldname: "program",
			fieldtype: "Link",
			options: "Program",
			reqd: 1
		}
		,
		{
			label: "Div",
			fieldname: "division",
			fieldtype: "Link",
			options: "Student Group",
			reqd: 1
		}
	])
}
function make_fieldgroup(parent, ddf_list) {
	fg = new frappe.ui.FieldGroup({
		"fields": ddf_list,
		"parent": parent
	});
	fg.make();

	return fg

}