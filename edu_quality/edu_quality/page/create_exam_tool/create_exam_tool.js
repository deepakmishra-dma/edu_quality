var globalPage = null
var filtersRef
frappe.pages['create-exam-tool'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'create-exam-tool',
		single_column: true
	});

	globalPage = page
	onLoad()
}

function onLoad() {
	frappe.require(["/assets/edu_quality/css/create-exam-tool.css"])

	const el = globalPage.wrapper.find('.container.page-body');

	filtersRef = make_fieldgroup(el, [
		{
			label: 'Name',
			fieldname: 'name',
			fieldtype: 'Data',

		},
		{
			label: 'School',
			fieldname: 'school',
			fieldtype: 'Link',
			options: "School"

		},
		{
			label: 'Class',
			fieldname: 'program',
			fieldtype: 'Link',
			options: "Program"

		},
		{
			label: 'Div',
			fieldname: 'division',
			fieldtype: 'Link',
			options: "Student Group"

		},
		{
			label: 'Order of Exam',
			fieldname: 'order_of_exam',
			fieldtype: 'Int',


		},
		{
			label: "Is Printable",
			fieldname: "is_printable",
			fieldtype: "Check"
		},
		{
			label: "Show in App",
			fieldname: "show_in_app",
			fieldtype: "Check"
		},
		{
			label: "Calculate Ranks",
			fieldname: "calculate_ranks",
			fieldtype: "Check"
		},
		{
			label: 'Report Print Configuration',
			fieldname: 'Report Print Configuration',
			fieldtype: 'Link',
			options: "Print Configuration"

		},
		{
			"label": "Child Table",
			fieldname: "subjects",
			fieldtype: "HTML",
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

