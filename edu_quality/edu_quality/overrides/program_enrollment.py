import frappe
from education.education.doctype.program_enrollment.program_enrollment import (
	ProgramEnrollment,
)
from frappe import _
from frappe.utils import comma_and, get_link_to_form, getdate
from frappe.utils.data import cstr

from edu_quality.edu_quality.server_scripts.student import (
	add_to_division,
	sync_and_sort_division_data,
)


class CustomProgramEnrollment(ProgramEnrollment):
	def on_submit(self):
		super().on_submit()
		self.sync_division_data()
		self.update_student_data()

	def invalidate_walsh_enrollments(self):
		student_doc = frappe.get_cached_doc("Student", self.student)
		for guardian in student_doc.guardians:
			user = frappe.db.get_value("Guardian", {"name": guardian.guardian}, "user")
			enrollment_key = f"walsh:enrollments_{user}"
			if frappe.cache().get_value(enrollment_key):
				frappe.cache().delete_value(enrollment_key)

	def update_subjects(self):
		self.courses = []
		program = frappe.get_doc("Program", self.program)
		for course in program.courses:
			self.append(
				"courses",
				{
					"course": course.course,
					"course_name": course.course_name,
				},
			)

	def before_save(self):
		self.update_subjects()

	def on_update_after_submit(self):
		#     self.sync_division_data()
		self.invalidate_walsh_enrollments()
		self.update_student_data()

	def before_update_after_submit(self):
		self.update_subjects()

	def validate_academic_year(self):
		start_date, end_date = frappe.db.get_value(
			"Academic Year", self.academic_year, ["year_start_date", "year_end_date"]
		)
		if self.enrollment_date:
			# if start_date and getdate(self.enrollment_date) < getdate(start_date):
			#     frappe.throw(
			#         _(
			#             "Enrollment Date cannot be before the Start Date of the Academic Year {0}"
			#         ).format(get_link_to_form("Academic Year", self.academic_year))
			#     )

			if end_date and getdate(self.enrollment_date) > getdate(end_date):
				frappe.throw(
					_("Enrollment Date cannot be after the End Date of the Academic Term {0}").format(
						get_link_to_form("Academic Year", self.academic_year)
					)
				)

	def validate_academic_term(self):
		start_date, end_date = frappe.db.get_value(
			"Academic Term", self.academic_term, ["term_start_date", "term_end_date"]
		)
		if self.enrollment_date:
			# if start_date and getdate(self.enrollment_date) < getdate(start_date):
			#     frappe.throw(
			#         _(
			#             "Enrollment Date cannot be before the Start Date of the Academic Term {0}"
			#         ).format(get_link_to_form("Academic Term", self.academic_term))
			#     )

			if end_date and getdate(self.enrollment_date) > getdate(end_date):
				frappe.throw(
					_("Enrollment Date cannot be after the End Date of the Academic Term {0}").format(
						get_link_to_form("Academic Term", self.academic_term)
					)
				)

	def _validate_selects(self):
		return
		if frappe.flags.in_import:
			self.sync_division_data()
			self.update_student_data()
			return

		for df in self.meta.get_select_fields():
			if df.fieldname == "naming_series" or not self.get(df.fieldname) or not df.options:
				continue

			options = (df.options or "").split("\n")

			# if only empty options
			if not filter(None, options):
				continue

			# strip and set
			self.set(df.fieldname, cstr(self.get(df.fieldname)).strip())
			value = self.get(df.fieldname)

			if value not in options and not (frappe.flags.in_test and value.startswith("_T-")):
				# show an elaborate message
				prefix = _("Row #{0}:").format(self.idx) if self.get("parentfield") else ""
				label = _(self.meta.get_label(df.fieldname))
				comma_options = '", "'.join(_(each) for each in options)

				frappe.throw(
					_('{0} {1} cannot be "{2}". It should be one of "{3}"').format(
						prefix, label, value, comma_options
					)
				)

	def update_student_data(self):
		fields = {
			"roll_no": self.roll_no,
			"tiffin_rack_no": self.tiffin_rack_no,
			"bus_service_required": self.transport_service_required,
			"school_house": self.school_house,
			"pickup_bus": self.pickup_bus,
			"drop_bus": self.drop_bus,
			"pickup_address": self.pickup_address,
			"drop_address": self.drop_address,
			"image": self.image,
			"program": self.program,
			"custom_division": self.student_group,
		}
		frappe.db.set_value("Student", self.student, fields)

	def sync_division_data(self):
		if frappe.db.exists(
			"Student Group Student",
			{"parent": self.student_group, "student": self.student},
		):
			return
		roll_no = add_to_division(self, self.student_group, add_log=False)
		self.roll_no = roll_no
		self.save(ignore_permissions=True)
		self.reload()
		# After adding student to division, sync and sort division data
		sync_and_sort_division_data(self.student_group)


def sync_student_data():
	"""
	Cron job to sync student data from Program Enrollment to Student
	"""
	academic_year = frappe.get_value("Academic Year", {"custom_current_academic_year": 1})
	fetch_fields = [
		"student",
		"program",
		"student_group",
		"roll_no",
		"tiffin_rack_no",
		"transport_service_required",
		"school_house",
		"pickup_bus",
		"drop_bus",
		"pickup_address",
		"drop_address",
	]
	pe_list = frappe.db.get_all(
		"Program Enrollment",
		{"academic_year": academic_year, "docstatus": 1},
		fetch_fields,
	)

	# Fetch all student groups in one call
	student_groups = {
		sg.name: sg.student_group_name
		for sg in frappe.get_all("Student Group", fields=["name", "student_group_name"])
	}

	for pe in pe_list:
		division = student_groups.get(pe.student_group)
		fields = {
			"roll_no": pe.roll_no,
			"tiffin_rack_no": pe.tiffin_rack_no,
			"bus_service_required": pe.transport_service_required,
			"school_house": pe.school_house,
			"pickup_bus": pe.pickup_bus,
			"drop_bus": pe.drop_bus,
			"pickup_address": pe.pickup_address,
			"drop_address": pe.drop_address,
			"program": pe.program,
			"custom_division": pe.student_group,
		}
		frappe.db.set_value("Student", pe.student, fields)

	frappe.db.commit()
