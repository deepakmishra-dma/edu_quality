# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import csv
import datetime
from io import StringIO

import frappe
import frappe.realtime
import requests
from frappe import _
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
from frappe.utils.data import get_datetime, getdate

from edu_quality.api.google_service_auth import GoogleServiceAccountAuth


class PTMScheduler(Document):
	@frappe.whitelist()
	def get_teacher(self):
		if self.teacher_alias:
			teachers = frappe.get_all(
				"Teacher Alias Group", filters={"alias": self.teacher_alias}, pluck="parent"
			)
			teacher = frappe.get_value(
				"Instructor", {"instructor_name": ["in", teachers], "custom_school": self.branch}
			)
			return teacher


@frappe.whitelist()
def check_file_permission(file_url):
	try:
		# Check if the file exists and get its details
		file_doc = frappe.get_doc("File", {"file_url": file_url})

		# Check if the file is private or public
		if file_doc.is_private:
			return {"status": "failed", "message": _("File is private")}
		else:
			return {"status": "success", "message": _("File is public")}
	except Exception as e:
		return {"status": "failed", "message": str(e)}


@frappe.whitelist()
def import_ptm_schedule_from_url(url):
	try:
		origin = frappe.request.headers.get("Origin")
		full_url = origin + url
		response = requests.get(full_url)
		response.raise_for_status()
		return import_ptm_schedule_background(response.text)
	except Exception as e:
		frappe.log_error(f"Error importing PTM schedule: {str(e)}", "PTM Schedule Import")
		return {"status": "failed", "message": str(e)}
	finally:
		# Disconnect database connection
		print("db closed")
		# frappe.db.close()


# def import_ptm_schedule_background(csv_content):
# 	try:
# 		csv_reader = csv.reader(StringIO(csv_content))
# 		total_rows = sum(1 for row in csv_reader) - 1  # Excluding header row
# 		csv_reader = csv.reader(StringIO(csv_content))
# 		next(csv_reader)  # Skip header row

# 		for idx, row in enumerate(csv_reader):
# 			acad_year, branch, cls_div, teacher_name, subject, group, period, gmeet, slot, date_str = row
# 			day = date_str.split(", ")[0]
# 			date = get_formatted_date(date_str)
# 			ptm_scheduler = frappe.new_doc("PTM Scheduler")
# 			ptm_scheduler.academic_year = acad_year
# 			ptm_scheduler.branch = branch.strip()
# 			ptm_scheduler.division = get_division(divStr=cls_div, branch=branch, academic_year=acad_year)
# 			ptm_scheduler.teacher_alias = teacher_name
# 			ptm_scheduler.teacher = get_teacher_from_alias(teacher_name.strip(),branch.strip())
# 			ptm_scheduler.subject = subject
# 			ptm_scheduler.group = group
# 			ptm_scheduler.period = period
# 			ptm_scheduler.slot = format_time_slot(slot)
# 			ptm_scheduler.date = date
# 			ptm_scheduler.day = day
# 			ptm_scheduler.save()
# 			progress = (idx + 1) * 100 // total_rows

# 			# Publish progress
# 			frappe.realtime.publish_progress(progress, title="Import PTM Scheduler", description=f"{idx+1}/{total_rows} rows processed")


# 		frappe.db.commit()
# 		return {"status": "success", "message": _("PTM schedule imported successfully")}
# 	except Exception as e:
# 		frappe.log_error(message=f"Error importing PTM schedule background: {str(e)}", title="PTM Schedule Import Background")
# 		return {"status": "failed", "message": str(e)}


def import_ptm_schedule_background(csv_content):
	errors = []
	try:
		csv_reader = csv.reader(StringIO(csv_content))
		total_rows = sum(1 for _ in csv_reader) - 1  # Excluding header row
		csv_reader = csv.reader(StringIO(csv_content))
		next(csv_reader)  # Skip header row

		for idx, row in enumerate(csv_reader, start=1):
			try:
				acad_year, branch, cls_div, teacher_name, subject, group, period, gmeet, slot, date_str = row
				day = date_str.split(", ")[0]
				date = get_formatted_date(date_str)
				ptm_scheduler = frappe.new_doc("PTM Scheduler")
				ptm_scheduler.academic_year = acad_year
				ptm_scheduler.branch = branch.strip()
				ptm_scheduler.division = get_division(divStr=cls_div, branch=branch, academic_year=acad_year)
				ptm_scheduler.teacher_alias = teacher_name
				ptm_scheduler.teacher = get_teacher_from_alias(teacher_name.strip(), branch.strip())
				ptm_scheduler.subject = subject
				ptm_scheduler.group = group
				ptm_scheduler.period = period
				ptm_scheduler.slot = format_time_slot(slot)
				ptm_scheduler.date = date
				ptm_scheduler.day = day
				ptm_scheduler.save()
				progress = idx * 100 // total_rows

				# Publish progress
				frappe.realtime.publish_progress(
					progress, title="Import PTM Scheduler", description=f"{idx}/{total_rows} rows processed"
				)
			except Exception as e:
				err = [idx, str(e)]
				errors.append(err)
				# Rollback changes

		if errors:
			frappe.db.rollback()
			error_message = "Error importing PTM schedule background:<br>"
			error_message += "<table>"
			error_message += "<tr><th>Row No</th><th>Error Message</th></tr>"
			for err in errors:
				error_message += f"<tr><td>{err[0]}</td><td>{err[1]}</td></tr>"
			error_message += "</table>"
			return {"status": "failed", "message": error_message}
		frappe.db.commit()
		return {"status": "success", "message": _("PTM schedule imported successfully")}
	except Exception as e:
		frappe.log_error(
			message=f"Error importing PTM schedule background: {str(e)}",
			title="PTM Schedule Import Background",
		)
		return {"status": "failed", "message": str(e)}


def is_number(n):
	try:
		return int(n)
	except:
		return False


def format_time_slot(time_slot):
	def convert_to_12_hour_format(time_str):
		# Parse time string
		time_obj = datetime.datetime.strptime(time_str, "%H:%M")
		# Convert to 12-hour format
		time_12_hour = time_obj.strftime("%I:%M %p")
		return time_12_hour

	# Split time slot into start and end times
	start_time, end_time = time_slot.split(" - ")
	# Convert start and end times to 12-hour format
	start_time_12_hour = convert_to_12_hour_format(start_time)
	end_time_12_hour = convert_to_12_hour_format(end_time)
	# Format the time slot
	formatted_time_slot = f"{start_time_12_hour} - {end_time_12_hour}"
	return formatted_time_slot


def get_prefix(divStr):
	if divStr[0].lower() == "n":
		return divStr[1:] + "-Nursery"
	elif divStr[0].lower() == "s":
		return divStr[1:] + "-Senior KG"
	elif divStr[0].lower() == "j":
		return divStr[1:] + "-Junior KG"


def get_division(divStr, branch, academic_year):
	if len(divStr) == 2:
		if is_number(divStr[0]):
			return divStr[1] + "-" + divStr[0] + "-" + branch + "-" + academic_year
		else:
			return get_prefix(divStr) + "-" + branch + "-" + academic_year
	elif len(divStr) == 3:
		if is_number(divStr[0]) and (is_number(divStr[1]) or divStr[1] == "0"):
			return divStr[2] + "-" + divStr[:2] + "-" + branch + "-" + academic_year
		else:
			return get_prefix(divStr) + "-" + branch + "-" + academic_year


def get_teacher_from_alias(alias, branch):
	error_raised = False  # Flag to track if error has been raised
	try:
		teacher_name_doc = frappe.get_all(
			"Teacher Alias Group", filters={"alias": alias}, fields=["parent", "name"]
		)
		if len(teacher_name_doc):
			for i in teacher_name_doc:
				teacher_doc = frappe.get_doc("Instructor", i.get("parent"))
				if branch == teacher_doc.custom_school:
					return i.parent
		error_raised = True  # Set flag to True if no teacher is found
		raise Exception(f"No Teacher linked with Alias {alias} for School {branch} ")
	except Exception as e:
		if not error_raised:  # Check if error has been raised before
			error_raised = True  # Set flag to True if error is being raised now
			raise Exception(f"No Teacher linked with Alias {alias} for School {branch} with error: {str(e)} ")
		else:
			raise e  # Re-raise the exception if it has been raised before


# return False


def get_formatted_date(date_str):
	# Define the format of the date string
	date_format = "%A, %d %B %Y"
	# Convert the date string to a datetime object
	date_object = datetime.datetime.strptime(date_str, date_format)
	return getdate(date_object)


@frappe.whitelist()
def generate_meeeting(summary, description, start_time, imporsonate_user):
	try:
		auth = GoogleServiceAccountAuth("calendar")
		meet_url = auth.create_meet(
			summary=summary,
			description=description,
			start_time=get_datetime(start_time),
			duration_minutes=24 * 60 * 6,
			imporsonate_user=imporsonate_user,
		)
		return meet_url
	except Exception as e:
		raise e


@frappe.whitelist()
def generate_meeting_function(items, summary, imporsonate_user, regenerate=False):
	try:
		items = frappe.parse_json(items) if isinstance(items, str) else items
		filters = [["name", "in", items]]

		if not regenerate:
			filters.append(["is_gmeet_generated", "=", 0])

		ptm_schedules_list = frappe.get_all(
			"PTM Scheduler", filters=filters, fields=["name", "teacher", "division", "gmeet_link", "date"]
		)
		if not len(ptm_schedules_list):
			return {"status": "failed", "message": "Gmeet Already Generated for: {}".format(",".join(items))}

		division_list = list(set([i.get("division") for i in ptm_schedules_list]))
		div_meeting_map = {}

		current_start_date_ac = frappe.db.get_value(
			"Academic Year", {"custom_current_academic_year": 1}, "year_start_date"
		)
		for div in division_list:
			gmeet_link = generate_meeeting(
				summary=summary,
				description="PTM Meeting Summary",
				start_time=current_start_date_ac,
				imporsonate_user=imporsonate_user,
			)

			div_meeting_map[div] = gmeet_link

		same_group_division_and_ptm = {}

		for ptm in ptm_schedules_list:
			if ptm.get("division") in same_group_division_and_ptm:
				same_group_division_and_ptm[ptm.get("division")].append(ptm.get("name"))
			else:
				same_group_division_and_ptm[ptm.get("division")] = [ptm.get("name")]

		for div, ptms in same_group_division_and_ptm.items():
			query = "UPDATE `tabPTM Scheduler` SET gmeet_link = %(gmeet_link)s, is_gmeet_generated = 1 WHERE name IN %(ptm_list)s"
			frappe.db.sql(query, {"gmeet_link": div_meeting_map[div], "ptm_list": tuple(set(ptms))})

		return {"status": "success", "message": "Gmeet Generated Successfully."}

	except Exception as e:
		frappe.log_error(f"Error generating Gmeet: {str(e)}", "Generate Meeting Function")
		return {"status": "failed", "message": str(e)}


@frappe.whitelist()
def get_recording_of_gmeet():
	try:
		meet_id = "ckm5241lp2up12stg4numuna6g"
		auth = GoogleServiceAccountAuth("calendar")
		meeting_details = auth.get_meeting_details(event_id=meet_id)
		print(meeting_details)
		return meeting_details
	except Exception as e:
		raise e
