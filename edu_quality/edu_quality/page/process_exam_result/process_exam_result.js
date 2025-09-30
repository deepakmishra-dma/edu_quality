var globalPage
var filtersRef
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

	filtersRef = make_fieldgroup(el, [
		{
			label: 'Academic Year',
			fieldname: 'acad_year',
			fieldtype: 'Link',
			options: "Academic Year",
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
function addProcessButton() {
	globalPage.set_primary_action('Process Result', processResult)
}
function processResult() {
	frappe.confirm('Are you sure you want to process the result for the selected filters',
		() => {

		}, () => {
			// action to perform if No is selected
		})
}
async function processResult() {
	const acad_year = filtersRef.get_value("acad_year")
	const school = filtersRef.get_value("school")
	const program = filtersRef.get_value("program")
	const division = filtersRef.get_value("division")
	const assess_group = filtersRef.get_value("exam_name")

	data = await frappe.call({
		"method": "edu_quality.api.exam_result.process_result",
		args: {
			academic_year: acad_year,
			school: school,
			program: program,
			division: division,
			assessment_group: assess_group
		}
	})

	if (data?.message?.errors) {
		
	}
}
function make_fieldgroup(parent, ddf_list) {
	fg = new frappe.ui.FieldGroup({
		"fields": ddf_list,
		"parent": parent
	});
	fg.make();

	return fg

}