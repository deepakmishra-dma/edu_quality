# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt
import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate
from frappe.utils.data import cstr

from edu_quality.public.py.walsh.admin import send_notification


class EventDetail(Document):
	def autoname(self):
		prefix = frappe.get_value("School", self.school, "prefix")
		self.name = f"{self.event_name} - {prefix}"

	def validate(self):
		invalid_chars = re.findall(r"[^a-zA-Z\.0-9/\\,\s_#@\-=+&]", self.event_name)

		if invalid_chars:
			invalid_chars_str = "".join(invalid_chars)
			message = f"Event Name contains invalid characters: {invalid_chars_str}. Only letters, numbers, spaces, and special characters: <b>. / \\ , _ # @ - = + & </b> are allowed."
			frappe.throw(_(message))

	def before_save(self):
		self.update_classes()
		if self.all_students:
			self.allowed_students = []

	def update_classes(self):
		event = frappe.get_doc("Event", self.event)

		# Remove classes that are no longer applicable
		self.classes_applicable_to = []

		# Add new applicable classes
		for cls in event.custom_classes:
			class_name = cls.get("class")
			self.append("classes_applicable_to", {"class": class_name})

	@frappe.whitelist()
	def get_students(self, args):
		refno = args.get("reference_number")
		student_status = args.get("student_status")
		students = []
		if refno:
			school = args.get("school")
			refno_list = refno.split(",")
			students = frappe.get_all(
				"Student",
				filters={
					"reference_number": ["in", refno_list],
					"school": school,
					"student_status": student_status,
				},
				fields=["name", "student_name"],
			)
		return students

	@frappe.whitelist()
	def send_registration_link(self, email_template=None):
		"""
		Send registration link to the students
		"""
		# Create the event participants. The Email will be sent to the students
		if not self.registration_email_template or not self.web_form:
			from frappe.integrations.doctype.webhook.webhook import enqueue_webhook

			frappe.enqueue(enqueue_webhook, doc=self, webhook={"name": "Event Detail Error"})
			return False
		else:
			frappe.enqueue(self.create_event_participants, email_template=email_template)
			return True

	def create_event_participants(self, email_template=None):
		"""
		Create event participants for the allowed students and send the registration link
		"""
		try:
			students = self.get_allowed_students()
			for student in students:
				if not frappe.db.exists("Event Participant", {"student": student, "event_detail": self.name}):
					participant = frappe.new_doc("Event Participant")
					participant.student = student
					participant.event_detail = self.name
					participant.save(ignore_permissions=True)
					participant.send_registration_link(email_template)
				else:
					participant = frappe.get_doc(
						"Event Participant", {"student": student, "event_detail": self.name}
					)
					participant.send_registration_link(email_template)
		except:
			frappe.log_error(
				f"Error while sending registration link for event: {self.name}", frappe.get_traceback()
			)

	def validate_students(self):
		if isinstance(self.student_status, str):
			statuses = [status.strip() for status in self.student_status.split(",")]
		else:
			statuses = []
		students = self.winning_students + self.participating_students

		for student in students:
			school = frappe.get_value("Student", student.student, "school")
			if school != self.school:
				frappe.throw(
					f"Student {student.student_name}({student.student}) does not belong to the school {self.school}"
				)

			student_status = frappe.get_value("Student", student.student, "student_status")
			if statuses and student_status not in statuses:
				frappe.throw(
					f"Student {student.student_name}({student.student}) status must be one of {self.student_status}"
				)

	def _validate_selects(self):
		if frappe.flags.in_import:
			self.validate_students()
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

	def send_reminders(self):
		"""
		Send reminders for the event based on the settings
		"""
		self.send_registration_reminders()
		self.send_event_reminders()

	def send_registration_reminders(self):
		"""
		Send registration reminder to the allowed to participate students
		"""
		today_date = getdate(nowdate())
		dates = get_event_dates("event_registration_reminder", self.name)
		for d in dates:
			if d.date == today_date:
				if not d.template_of_reminders:
					frappe.log_error(
						f"No template found for event registration reminders: {self.name} for date: {d.date}"
					)
					continue
				self.send_registration_link(d.template_of_reminders)

	def send_event_reminders(self):
		"""
		Send event reminder to the participating students
		"""
		today_date = getdate(nowdate())
		dates = get_event_dates("event_reminder", self.name)
		for d in dates:
			if d.date == today_date:
				if not d.template_of_reminders:
					frappe.log_error(f"No template found for event reminders: {self.name}")
					continue
				template = frappe.get_doc("Email Template", d.template_of_reminders)
				context = self.as_dict()
				subject = frappe.render_template(template.subject, context=context)
				message = frappe.render_template(template.response, context=context)
				frappe.sendmail(
					recipients=self.get_student_emails(participating=True),
					subject=subject,
					message=message,
				)

	@frappe.whitelist()
	def get_allowed_students(self):
		"""
		Get the allowed students
		"""
		filters = {"school": self.school}
		if not self.all_students:
			students = frappe.get_all(
				"Event Student",
				{"parent": self.name, "parentfield": "allowed_students"},
				pluck="student",
			)
			if students:
				filters["name"] = ["in", students]
			else:
				return []
		else:
			classes = frappe.get_all("Classes", {"parent": self.name}, pluck="class")
			if classes:
				filters["program"] = ["in", classes]
			if self.student_status:
				statuses = [status.strip() for status in self.student_status.split(",")]
				filters["student_status"] = ["in", statuses]

		return frappe.get_all("Student", filters, pluck="name")

	def get_participating_students(self):
		"""
		Get the participating students
		"""
		students = frappe.get_all(
			"Student Data",
			{"parent": self.name, "parentfield": "participating_students"},
			pluck="student",
		)
		return students

	def get_student_emails(self, participating=False):
		"""
		Get the student emails based on the students
		Args:
		    students (list): List of students
		    participating (bool): True for participating students, False for allowed students
		"""
		if participating:
			students = self.get_participating_students()
		else:
			students = self.get_allowed_students()
		return frappe.get_all("Student", {"name": ["in", students]}, pluck="student_email_id")

	def send_app_notification(self, student, subject, message, is_raw_html=True, is_published=True):
		"""
		Send app notification for the event
		"""
		try:
			notice_id = self.create_school_notice(student, subject, message, is_raw_html, is_published)
			send_notification(student, subject, notice_id)
		except Exception as e:
			frappe.log_error(
				f"Error while sending app notification for event: {self.name}", frappe.get_traceback()
			)

	def create_school_notice(self, student, subject, message, is_raw_html=True, is_published=True):
		"""
		Create school notice for the event
		"""
		academic_year = frappe.get_value("Academic Year", {"custom_current_academic_year": 1})
		pe = frappe.get_value(
			"Program Enrollment",
			{"student": student, "academic_year": academic_year},
			["student_group", "program"],
			as_dict=True,
		)
		student_status = frappe.get_value("Student", student, "student_status")

		notice_data = {
			"student": student,
			"academic_year": academic_year,
			"school": self.school,
			"division": pe.student_group if pe.student_group else None,
			"student_status": student_status,
			"subject": subject,
			"notice": message,
			"is_raw_html": is_raw_html,
			"class": pe.program if pe.program else None,
		}

		notice = frappe.get_doc({"doctype": "School Notice", **notice_data})
		if hasattr(notice, "is_published"):
			notice.is_published = is_published
		notice.save(ignore_permissions=True)
		return notice.name


def get_event_dates(type, parent):
	"""
	Get the event dates based on the type and parent
	"""
	return frappe.get_all(
		"Event Date",
		{"parent": parent, "parentfield": type},
		["date", "template_of_reminders"],
	)


def calculate_reminder_date(date_from, days_before):
	"""
	Calculate the reminder date based on the date_from and days_before
	"""
	if date_from:
		return getdate(add_days(date_from, -abs(days_before)))
	return None


def send_event_reminder():
	"""
	Send event reminder
	"""
	events = frappe.get_all("Event Detail", {"event_starts_on": [">=", nowdate()]})
	for event in events:
		event_doc = frappe.get_doc("Event Detail", event.name)
		event_doc.send_reminders()


@frappe.whitelist()
def add_participating_students(student_data):
	student_data = frappe.parse_json(student_data)
	parent_name = student_data.get("parent")
	student = student_data.get("student")
	parent_doc = frappe.get_doc("Event Detail", parent_name)
	if not frappe.db.exists(
		"Student Data",
		{
			"student": student,
			"parent": parent_name,
			"parentfield": "participating_students",
		},
	):
		parent_doc.append(
			"participating_students",
			{
				"student": student_data.get("student"),
				"student_name": student_data.get("student_name"),
				"refno": student_data.get("refno"),
			},
		)
		parent_doc.save()
		return True
	return False
