# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt
import re
import shutil
from pathlib import Path

import frappe
from frappe import _
from frappe.model.document import Document

from edu_quality.common.utils.auth import set_user_permissions


class EventParticipant(Document):
	def on_update(self):
		prev_doc = self.get_doc_before_save()
		if not prev_doc:
			return
		if self.payment_required:
			return
		user = frappe.session.user
		if "Guardian" in frappe.get_roles(user):
			self.submit()

	@frappe.whitelist()
	def get_participant_details(self):
		return frappe.json.loads(self.data)

	def after_insert(self):
		self.form_hash = frappe.generate_hash(self.name, length=20)
		# Set Payment Required and Amount based on the Event Detail and Web Form
		if self.event_detail:
			web_form_name = frappe.get_value("Event Detail", self.event_detail, "web_form")
			web_form = frappe.get_value("Web Form", web_form_name, ["amount", "accept_payment"], as_dict=True)
			if web_form:
				self.outstanding_amount = web_form.amount
				self.payment_required = web_form.accept_payment

		self.save(ignore_permissions=True)
		guardian = frappe.get_all("Student Guardian", {"parent": self.student}, pluck="guardian")
		users = frappe.get_all("Guardian", {"name": ("in", guardian)}, pluck="user")
		for user in users:
			set_user_permissions(user, self.doctype, self.name)

	def on_trash(self):
		user_permission = frappe.get_all(
			"User Permission", {"allow": self.doctype, "for_value": self.name}, pluck="name"
		)
		if user_permission:
			for perm in user_permission:
				frappe.delete_doc("User Permission", perm, ignore_permissions=True)

	def send_registration_link(self, email_template=None):
		# Early exit if paid
		if self.payment_status == "Paid":
			return

		# Early exit if no student is associated
		guardian = frappe.get_all("Student Guardian", {"parent": self.student}, pluck="guardian")
		if not guardian:
			return

		emails = frappe.get_all("Guardian", {"name": ("in", guardian)}, pluck="email_address")
		# Early exit if no emails are found
		if not emails:
			return

		# Get web form URL
		web_form = frappe.get_value("Event Detail", self.event_detail, "web_form")
		route = frappe.get_value("Web Form", web_form, "route")

		form_url = f"{frappe.utils.get_url()}/get-web-form?hash={self.form_hash}&redirect_to={route}"

		# Determine the email template to use
		if not email_template:
			email_template = frappe.get_value(
				"Event Detail", self.event_detail, "registration_email_template"
			)

		# Build context
		context = {"form_url": form_url, "event_detail": self.event_detail}

		# Determine subject and message
		if email_template and web_form:
			subject = frappe.render_template(
				frappe.get_value("Email Template", email_template, "subject"), context
			)
			message = frappe.render_template(
				frappe.get_value("Email Template", email_template, "response"), context
			)
			# Send email
			frappe.sendmail(recipients=emails, subject=subject, message=message)

	def on_submit(self):
		if self.payment_required:
			self.outstanding_amount = max(self.outstanding_amount, 0)

			if self.payment_status != "Paid" or self.outstanding_amount > 0:
				frappe.throw("Payment is pending, please make the payment to submit the form")
			else:
				self.create_payment_entry()
				try:
					from nextai.funnel.custom_trigger import trigger_event

					trigger_event(doc=self, event_name="event_payment_success")
				except ImportError:  # Assuming the specific exception for module not found
					frappe.log_error("Chatnext is not installed", "ImportError")

		if not frappe.db.exists("Student Data", {"student": self.student, "parent": self.event_detail}):
			participant = frappe.new_doc("Student Data")
			participant.student = self.student
			participant.student_name = self.student_name
			participant.refno = self.refno
			participant.event_participant_link = self.name
			participant.payment_status = self.payment_status if self.payment_required else None
			participant.parent = self.event_detail
			participant.parenttype = "Event Detail"
			participant.parentfield = "participating_students"
			participant.save(ignore_permissions=True)

	def validate_payment(self, data=None):
		if data:
			amount = data.get("amount") or 0
			if isinstance(amount, str):
				amount = float(amount)
			self.payment_status = "Paid"
			self.outstanding_amount -= amount
			self.paid_amount = amount
			self.paid_date = frappe.utils.today()
			self.save(ignore_permissions=True)
			self.submit()
			return {"status": "success", "message": "Payment Successful"}
		else:
			return {"status": "error", "message": "Payment data not found"}

	def create_payment_entry(self, posting_date=None, reference_date=None):
		try:
			user = frappe.session.user
			frappe.set_user("Administrator")
			paid_from = frappe.get_value("School", self.school, "event_account")
			company = frappe.get_value("Account", paid_from, "company")
			paid_to = frappe.get_value("Company", company, "default_easebuzz_account")
			cost_center = frappe.get_value("Company", company, "cost_center")
			payment_entry = frappe.get_doc(
				{
					"doctype": "Payment Entry",
					"payment_type": "Receive",
					"company": company,
					"cost_center": cost_center,
					"posting_date": posting_date or frappe.utils.nowdate(),
					"reference_date": reference_date or frappe.utils.nowdate(),
					"party_type": "Student",
					"party": self.student,
					"party_name": self.student_name,
					"paid_from": paid_from,
					"paid_to": paid_to,
					"paid_amount": self.paid_amount,
					"received_amount": self.paid_amount,
					"reference_doctype": self.doctype,  # 'Fees' or 'Fee Advance'
					"reference_name": self.name,
					"mode_of_payment": "Online",
					"reference_no": self.transaction_id,
					"school": self.school,
					"program": self.get("class"),
				}
			)
			payment_entry.insert(ignore_permissions=True)
			payment_entry.submit()
			frappe.set_user(user)
		except:
			frappe.log_error("Error While Creating Payment Entry for event", frappe.get_traceback())


@frappe.whitelist()
def export_participant_data(event_detail):
	data = []
	participant = frappe.get_all(
		"Event Participant",
		filters={"event_detail": event_detail},
		fields=["name", "data"],
	)
	for p in participant:
		data.append(frappe.json.loads(p.data))
	return data


@frappe.whitelist()
def get_data(**kwargs):
	data = {}

	# Fetch event detail data if provided
	event_detail = kwargs.get("event_detail")
	if event_detail:
		event_data = frappe.get_value(
			"Event Detail", event_detail, ["event", "event_starts_on", "school"], as_dict=True
		)
		if event_data:
			data.update(event_data)

	# Fetch student data if reference number is provided
	refno = kwargs.get("refno")
	if refno:
		# Build filters dictionary
		filters = {"reference_number": refno}
		school = kwargs.get("school")
		if school:
			filters["school"] = school

		# Check if the user has access to the student data
		student = frappe.get_value(
			"Student",
			filters,
			["name", "student_name", "program"],
			as_dict=True,
		)
		if student:
			if frappe.has_permission("Student", "read", student.name):
				data.update(student)
			else:
				frappe.throw(_("You do not have permission to access this student's data"))

	return data


@frappe.whitelist()
def process_attachment(doctype, docname, file_url, field_name, field_label, old_file_url=None):
	try:
		if file_url:
			return rename_file(doctype, docname, file_url, field_name, field_label)
		elif old_file_url:
			files = frappe.get_all("File", {"file_url": old_file_url})
			for file in files:
				frappe.delete_doc("File", file.name)
	except Exception as e:
		frappe.log_error(f"Error while renaming file: {str(e)}", frappe.get_traceback())
		return False


def get_file_name(docname, ext, name_hash, field_label):
	text = f"{docname}-({field_label})"
	text = re.sub(r"\s+", "-", text.replace("-", " ").replace(".", " "))
	return f"{text}-{name_hash}{ext}"


def rename_file(doctype, docname, file_url, field_name, field_label):
	file_info = frappe.get_value("File", {"file_url": file_url})
	if not file_info:
		return False

	file_doc = frappe.get_doc("File", file_info)
	file_name = Path(file_doc.file_url).name
	ext = Path(file_name).suffix
	new_file_name = get_file_name(docname, ext, file_doc.name, field_label)
	old_file_path = file_doc.get_full_path()
	new_file_path = Path(old_file_path).parent / new_file_name
	if file_doc.is_private:
		file_url = f"/private/files/{new_file_name}"
	else:
		file_url = f"/files/{new_file_name}"
	shutil.move(old_file_path, new_file_path)

	file_doc.file_name = new_file_name
	file_doc.file_url = file_url
	file_doc.attached_to_doctype = doctype
	file_doc.attached_to_name = docname
	file_doc.attached_to_field = field_name
	file_doc.is_private = 0
	file_doc.save()

	return file_doc.file_url
