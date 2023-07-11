# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.model.mapper import get_mapped_doc
from frappe import _
from frappe.utils import cint, cstr, flt, money_in_words

class FeeAdvance(Document):
	def before_save(self):
		for student in self.students:
			student.total_students = get_total_students(student.student_group, self.academic_year)
		old_doc = self.get_doc_before_save()
		if old_doc:
			if (old_doc.fee_structure == self.fee_structure) and old_doc.payment_term == self.payment_term:
				return
		fee_structure = frappe.get_doc("Fee Structure", self.fee_structure)
		self.components = []
		percent = frappe.db.get_value("Payment Term",self.payment_term,'invoice_portion')
		self.amount = 0
		for component in fee_structure.components:
			self.amount += component.amount * percent/100
			self.append("components",{
				'fees_category': component.fees_category,
				'description': component.description,
				'amount': component.amount * percent/100
			})
		
	
	@frappe.whitelist()
	def create_fees(self):
		self.db_set("fee_creation_status", "In Process")
		frappe.publish_realtime(
			"fee_advance_progress", {"progress": "0", "reload": 1}, user=frappe.session.user
		)

		total_records = sum([int(d.total_students) for d in self.students])
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
				fee_advance=self.name,
			)
		else:
			generate_fee(self.name)


def generate_fee(fee_advance):
	doc = frappe.get_doc("Fee Advance", fee_advance)
	error = False
	total_records = sum([int(d.total_students) for d in doc.students])
	created_records = 0

	if not total_records:
		frappe.throw(_("Please setup Students under Student Groups"))

	for d in doc.students:
		students = get_students(
			d.student_group, doc.academic_year, None, None
		)
		print(students)
		for student in students:
			try:
				fees_doc = get_mapped_doc(
					"Fee Advance",
					fee_advance,
					{"Fee Advance": {"doctype": "Fees", "field_map": {"name": "Fee Advance"}}},
				)
				print(fees_doc)
				fees_doc.posting_date = doc.posting_date
				fees_doc.student = student.student
				fees_doc.student_name = student.student_name
				fees_doc.program = student.program
				fees_doc.program_enrollment = student.enrollment
				fees_doc.student_batch = student.student_batch_name
				fees_doc.send_payment_request = 0
				fees_doc.payment_plan = None
				fees_doc.save()
				fees_doc.submit()
				created_records += 1
				frappe.publish_realtime(
					"fee_advance_progress",
					{"progress": str(int(created_records * 100 / total_records))},
					user=frappe.session.user,
				)

			except Exception as e:
				error = True
				err_msg = (
					frappe.local.message_log and "\n\n".join(frappe.local.message_log) or cstr(e)
				)

	if error:
		frappe.db.rollback()
		frappe.db.set_value("Fee Advance", fee_advance, "fee_creation_status", "Failed")
		frappe.db.set_value("Fee Advance", fee_advance, "error_log", err_msg)

	else:
		frappe.db.set_value("Fee Advance", fee_advance, "fee_creation_status", "Successful")
		frappe.db.set_value("Fee Advance", fee_advance, "error_log", None)

	frappe.publish_realtime(
		"fee_advance_progress", {"progress": "100", "reload": 1}, user=frappe.session.user
	)


def get_students(
	student_group, academic_year=None, academic_term=None, student_category=None
):
	conditions = ""
	if student_category:
		conditions = " and pe.student_category={}".format(frappe.db.escape(student_category))
	if academic_term:
		conditions += " and pe.academic_term={}".format(frappe.db.escape(academic_term))

	students = frappe.db.sql(
		"""
		select pe.student, pe.student_name, pe.program, pe.student_batch_name, pe.name as enrollment
		from `tabStudent Group Student` sgs, `tabProgram Enrollment` pe
		where
			pe.docstatus = 1 and pe.student = sgs.student
			and sgs.parent = %s and sgs.active = 1
			{conditions}
		""".format(
			conditions=conditions
		),
		(student_group),
		as_dict=1,
	)
	return students


@frappe.whitelist()
def get_total_students(
	student_group, academic_year=None, academic_term=None, student_category=None
):
	total_students = get_students(
		student_group, academic_year, academic_term, student_category
	)
	return len(total_students)
