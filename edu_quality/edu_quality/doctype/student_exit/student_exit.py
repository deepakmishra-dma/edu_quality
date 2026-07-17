# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


def date_to_words(date):
	return date.strftime("%d %B %Y")


class StudentExit(Document):
	def after_insert(self):
		self.requested_on = frappe.utils.nowdate()
		self.update_details()

	def before_save(self):
		self.update_details()

	@frappe.whitelist()
	def update_details(self):
		student = frappe.get_doc("Student", self.student)
		try:
			fee, deposit, account = student.check_deposit(deduct=1)
			self.deposit_amount = deposit
			self.pending_fees = student.check_pending_fee()
			if self.pending_fees:
				self.fees_status = "Unpaid"
			else:
				self.fees_status = "Paid"
			if student.guardians:
				for guardian in student.guardians:
					if guardian.relation == "Father":
						self.father_name = guardian.guardian_name
					elif guardian.relation == "Mother":
						self.mother_name = guardian.guardian_name
					else:
						guardian_name = guardian.guardian_name
				if not self.father_name:
					self.father_name = guardian_name
			self.dob_in_words = date_to_words(student.date_of_birth)
			self.get_fee_details()
			if self.cancellation_type != "Deduct from Deposit":
				self.refund_amount = self.deposit_amount
			elif self.deposit_amount >= self.pending_fees:
				self.refund_amount = self.deposit_amount - self.pending_fees
			else:
				self.refund_amount = 0
			self.get_subjects()
			self.get_attendance_details()
			# self.save()
		except Exception as e:
			frappe.log_error(title="Dep Error", message=frappe.get_traceback())
			self.deposit_amount = 0
			self.refund_amount = 0

	def get_attendance_details(self):
		academic_yr = frappe.get_doc("Academic Year", {"custom_current_academic_year": 1})
		total_days = frappe.db.count(
			"Attendance Entry",
			[
				[
					"Attendance Entry",
					"date",
					"Between",
					[academic_yr.year_start_date, academic_yr.year_end_date],
				],
				["Attendance Entry", "student", "=", self.student],
			],
		)
		total_present = frappe.db.count(
			"Attendance Entry",
			[
				[
					"Attendance Entry",
					"date",
					"Between",
					[academic_yr.year_start_date, academic_yr.year_end_date],
				],
				["Attendance Entry", "student", "=", self.student],
				["Attendance Entry", "status", "=", "Present"],
			],
		)
		self.total_working_days = total_days
		self.days_present = total_present
		if self.total_working_days:
			self.attendance_percentage = (self.days_present / self.total_working_days) * 100

	def get_subjects(self):
		current_yr = frappe.db.get_value("Academic Year", {"custom_current_academic_year": 1})
		pe_filter = {"academic_year": current_yr, "student": self.student, "docstatus": 1}
		program_enrollment_name = frappe.db.get_value("Program Enrollment", pe_filter)
		if not program_enrollment_name:
			return
		program_enrollment = frappe.get_doc("Program Enrollment", program_enrollment_name)
		self.last_class_studied = program_enrollment.program
		self.courses = []
		for course in program_enrollment.courses:
			self.append(
				"courses",
				{
					"course": course.course,
					"course_name": course.course_name,
				},
			)

	def get_fee_details(self):
		last_paid_fee = frappe.db.get_all(
			"Fees",
			filters=[["Fees", "student", "=", "SHFA21"], ["Payment Schedule", "outstanding", "=", 0]],
			order_by="academic_year desc",
			limit=1,
		)
		if last_paid_fee:
			self.fees_paid_upto = frappe.db.get_all(
				"Payment Schedule",
				{"parent": last_paid_fee[0].name, "outstanding": 0},
				"due_date",
				order_by="payment_term desc",
				limit=1,
			)[0].due_date
			fee = frappe.get_doc("Fees", last_paid_fee[0].name)
			for component in fee.components:
				if component.custom_discounts:
					self.discount_details = self.discount_details + ", " + component.custom_discounts
			self.discount_details = self.discount_details or "" + "Total Amount - " + str(fee.total_discount)

	def on_submit(self):
		if not self.cancellation_letter:
			frappe.throw("Cancellation Letter is required!")
		if not self.date_of_leaving:
			frappe.throw("Date of Leaving is required!")
		student = frappe.get_doc("Student", self.student)
		student.custom_cancellation_letter = self.cancellation_letter
		student.date_of_leaving = self.date_of_leaving
		# student.leaving_certificate_number = self.leaving_certificate_number
		student.save(ignore_permissions=True)
		student.cancel_student(self.academic_year, self.cancellation_type)
