# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from edu_quality.edu_quality.server_scripts.utils import current_academic_year

class AttendanceEntryPrint(Document):
	def on_submit(self):
		try:
			self.get_students()
		except Exception as e:
			frappe.logger('attendance_entry_print').exception(e)

	def get_students(self):
		students = frappe.db.get_list("Program Enrollment",[["Program Enrollment","academic_year","=",current_academic_year()],["Program Enrollment","student_group","in",[i.division for i in self.divisions]]],fields=['student','roll_no'])
		for student in students:
			self.append("students",student)
	
	def get_working_days(self):
		from datetime import timedelta
		days = [self.from_date + timedelta(days=x) for x in range((self.to_date-self.from_date).days)]
		holidays = frappe.db.get_all("Holiday",filter={'parent':self.holiday_list},fields=['holiday_date'])
		final = [str(day.day()) for day in days if day.date() not in [i.holiday_date for i in holidays]]
		self.db_set("working_days",",".join(final))

