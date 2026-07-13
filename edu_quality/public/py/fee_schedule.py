import frappe
from education.education.doctype.fee_schedule.fee_schedule import FeeSchedule
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import cstr


class CustomFeeSchedule(FeeSchedule):
	@frappe.whitelist()
	def create_fees(self):
		self.db_set("fee_creation_status", "In Process")
		frappe.publish_realtime(
			"fee_schedule_progress", {"progress": "0", "reload": 1}, user=frappe.session.user
		)

		total_records = sum([int(d.total_students) for d in self.student_groups])
		if total_records > 10:
			frappe.msgprint(
				_(
					"""Fee records will be created in the background.
                In case of any error the error message will be updated in the Schedule."""
				)
			)
			enqueue(
				generate_fee,
				queue="default",
				timeout=6000,
				event="generate_fee",
				fee_schedule=self.name,
			)
		else:
			generate_fee(self.name)


def generate_fee(fee_schedule):
	doc = frappe.get_doc("Fee Schedule", fee_schedule)
	error = False
	total_records = sum([int(d.total_students) for d in doc.student_groups])
	created_records = 0

	if not total_records:
		frappe.throw(_("Please setup Students under Student Groups"))

	for d in doc.student_groups:
		students = get_students(d.student_group, doc.academic_year, doc.academic_term, doc.student_category)
		for student in students:
			try:
				fees_doc = get_mapped_doc(
					"Fee Schedule",
					fee_schedule,
					{"Fee Schedule": {"doctype": "Fees", "field_map": {"name": "Fee Schedule"}}},
				)
				fees_doc.posting_date = doc.posting_date
				fees_doc.student = student.student
				fees_doc.student_name = student.student_name
				fees_doc.program = student.program
				fees_doc.program_enrollment = student.enrollment
				fees_doc.student_batch = student.student_batch_name
				fees_doc.send_payment_request = doc.send_email
				fees_doc.payment_plan = doc.payment_plan
				fees_doc.save()
				fees_doc.submit()
				created_records += 1
				frappe.publish_realtime(
					"fee_schedule_progress",
					{"progress": str(int(created_records * 100 / total_records))},
					user=frappe.session.user,
				)

			except Exception as e:
				error = True
				err_msg = frappe.local.message_log and "\n\n".join(frappe.local.message_log) or cstr(e)

	if error:
		frappe.db.rollback()
		frappe.db.set_value("Fee Schedule", fee_schedule, "fee_creation_status", "Failed")
		frappe.db.set_value("Fee Schedule", fee_schedule, "error_log", err_msg)

	else:
		frappe.db.set_value("Fee Schedule", fee_schedule, "fee_creation_status", "Successful")
		frappe.db.set_value("Fee Schedule", fee_schedule, "error_log", None)

	frappe.publish_realtime(
		"fee_schedule_progress", {"progress": "100", "reload": 1}, user=frappe.session.user
	)


def get_students(student_group, academic_year, academic_term=None, student_category=None):
	conditions = ""
	if student_category:
		conditions = f" and pe.student_category={frappe.db.escape(student_category)}"
	if academic_term:
		conditions += f" and pe.academic_term={frappe.db.escape(academic_term)}"

	students = frappe.db.sql(
		f"""
		select pe.student, pe.student_name, pe.program, pe.student_batch_name, pe.name as enrollment
		from `tabStudent Group Student` sgs, `tabProgram Enrollment` pe
		where
			pe.docstatus = 1 and pe.student = sgs.student and pe.academic_year = %s
			and sgs.parent = %s and sgs.active = 1
			{conditions}
		""",
		(academic_year, student_group),
		as_dict=1,
	)
	return students
