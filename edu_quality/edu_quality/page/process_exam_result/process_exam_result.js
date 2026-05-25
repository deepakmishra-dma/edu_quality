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
			label: "Class",
			fieldname: "program",
			fieldtype: "Link",
			options: "Program",
			reqd: 1,
			get_query: function (txt) {

				const school = filtersRef.get_value("school")


				return { filters: { "school": school } };
			}
		}
		,
		{
			label: "Exam Name",
			fieldname: "exam_name",
			fieldtype: "Link",
			options: "Assessment Group",
			reqd: 1,
			"get_query": function (txt) {
				const academic_year = filtersRef.get_value("acad_year")
				const school = filtersRef.get_value("school")
				const program = filtersRef.get_value("program")
				return { filters: { "custom_is_composite": 0, "custom_academic_year": academic_year, "custom_school": school, "custom_program": program } };
			}
		},
		{
			label: "Div",
			fieldname: "division",
			fieldtype: "Link",
			options: "Student Group",
			get_query: () => {
				const program = filtersRef.get_value("program");
				const academic_year = filtersRef.get_value("acad_year");
				return { filters: { "program": program, academic_year: academic_year } };
			},
			onchange: () => {
				if (filtersRef.get_value("division")) {
					filtersRef.set_value("ref_nos", "");
					filtersRef.set_df_property("ref_nos", "read_only", 1);
				} else {
					filtersRef.set_df_property("ref_nos", "read_only", 0);
				}

			}
		},
		{
			label: "Ref Numbers",
			fieldname: "ref_nos",
			fieldtype: "Text",
			options: "",
			description: "Enter Ref Nos Separated by , to process only the specified ones",
			onchange: () => {
				if (filtersRef.get_value("ref_nos")) {
					filtersRef.set_value("division", "");
					filtersRef.set_df_property("division", "read_only", 1);
				} else {
					filtersRef.set_df_property("division", "read_only", 0);
				}

			}
		},
		{
			label: "Create Group Result Only",
			fieldname: "create_toppers_only",
			fieldtype: "Check",
			options: "",
			description: "Doesn't cancel assessment result and  only recaclulate assessment group result"
		},
	])
	if (frappe.route_options) {
		updateFilters()
	}
	addProcessButton()
}

function updateFilters() {
	filtersRef.set_value("acad_year", frappe.route_options.academic_year)
	filtersRef.set_value("school", frappe.route_options.school)
	filtersRef.set_value("program", frappe.route_options.program)
	filtersRef.set_value("exam_name", frappe.route_options.exam)
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
	const ref_nos = filtersRef.get_value("ref_nos")
	const create_toppers_only = filtersRef.get_value("create_toppers_only")

	if (!acad_year || !school || !program || !assess_group) {
		frappe.throw(__('Academic Year or School or Program or Exam Group is required'))
		return
	}
	frappe.confirm('If there are submitted results they will be cancelled and new ones will be created, Are you sure you want to proceed?', async () => {
		data = await frappe.call({
			"method": "edu_quality.api.exam_result.process_result",
			args: {
				academic_year: acad_year,
				school: school,
				program: program,
				division: division,
				assessment_group: assess_group,
				ref_nos: ref_nos,
				create_toppers_only: create_toppers_only || 0
			}
		})

		if (data?.message?.errors) {
			console.log("Something Went Wrong", data?.message?.errors)
		}
	}, () => {

	})


}
function make_fieldgroup(parent, ddf_list) {
	fg = new frappe.ui.FieldGroup({
		"fields": ddf_list,
		"parent": parent
	});
	fg.make();

	return fg

}