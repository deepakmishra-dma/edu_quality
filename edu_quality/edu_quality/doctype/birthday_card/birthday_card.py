# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe.auth import LoginManager
from frappe.model.document import Document
from frappe.utils import getdate
from weasyprint import HTML

from edu_quality.edu_quality.server_scripts.student_applicant import generate_hash
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


class BirthdayCard(Document):
	def before_insert(self, method=None):
		try:
			card_traits_meta_fields = frappe.get_meta("Birthday Card Trait").get("fields", [])

			trait_select = [i for i in card_traits_meta_fields if i.get("fieldname") == "trait_type"]

			if trait_select:
				trait_select = trait_select[0].options.split("\n")

			for trait in trait_select:
				self.append("traits", {"trait_type": trait})
		except Exception as e:
			frappe.log_error(title="BirthdayCard Error", message=frappe.get_traceback())

	def after_insert(self, method=None):
		self.form_hash = generate_hash(self.name)
		self.save(ignore_permissions=True)
		set_guardian_permissions(self)


@frappe.whitelist(allow_guest=True)
def get_birthday_form(hash):
	if frappe.db.exists("Birthday Card", {"form_hash": hash}):
		birthday_card = frappe.db.get_value("Birthday Card", {"form_hash": hash}, "name")
		if frappe.db.exists(
			"User Permission",
			{"allow": "Birthday Card", "for_value": birthday_card},
		):
			user = frappe.db.get_value(
				"User Permission",
				{"allow": "Birthday Card", "for_value": birthday_card},
				"user",
			)
			login_manager = LoginManager()
			login_manager.login_as(user)
		return frappe.utils.get_url() + "/birthday-details/" + birthday_card + "/edit"

	frappe.throw("User Not set for this Birthday Card!")
	frappe.throw("Birthday Card Not Found!")


def set_guardian_permissions(doc):
	student_doc = frappe.get_doc("Student", doc.student)
	for guardian in student_doc.guardians:
		user = frappe.db.get_value("Guardian", guardian.guardian, "user")
		if not user:
			continue
		if not frappe.db.exists(
			"User Permission",
			{"user": user, "allow": "Birthday Card", "for_value": doc.name},
		):
			perm = frappe.new_doc("User Permission")
			perm.user = user
			perm.allow = "Birthday Card"
			perm.for_value = doc.name
			perm.insert(ignore_permissions=True)


@frappe.whitelist()
def print_birthday_card(birthday_cards):
	"""
	Generate and print birthday cards for students.

	Args:
	    birthday_cards (list): A list of tuples containing the birthday card name and the year.

	Returns:
	    bytes: The PDF file content.
	"""
	try:
		base_url = frappe.utils.get_url()
		cards = [get_birthday_card_data(card, year) for card, year in birthday_cards]
		template = frappe.render_template(
			"edu_quality/templates/pdf/birthday_card.html",
			{"cards": cards},
		)

		html = HTML(string=template, base_url=base_url)
		main_doc = html.render()
		main_pdf = main_doc.write_pdf()

		filename = f"Birthday Card ({frappe.utils.today()}).pdf".replace(" ", "-").replace("/", "-")

		frappe.local.response.filename = filename
		frappe.local.response.filecontent = main_pdf
		frappe.local.response.type = "pdf"
		return main_pdf
	except Exception as e:
		frappe.log_error("Print Birthday Card Error", frappe.get_traceback())


@frappe.whitelist()
def print_birthday_cards(from_date, to_date, student_status=None, school=None):
	"""
	Generate and print birthday cards for students within a specified date range.

	Args:
	    from_date (str): The start date in 'DD-MM-YYYY' format.
	    to_date (str): The end date in 'DD-MM-YYYY' format.
	    student_status (str, optional): The status of the students to filter by.
	    school (str, optional): The school to filter students by.

	Returns:
	    list: A list of tuples containing the birthday card name and the year.
	"""
	from_date = getdate(from_date)
	to_date = getdate(to_date)
	filters = {}
	if student_status:
		filters["student_status"] = student_status
	if school:
		filters["school"] = school
	students = frappe.get_all("Student", filters=filters, pluck="name")
	birthday_cards = frappe.get_all(
		"Birthday Card",
		filters={"student": ["in", students]},
		fields=["name", "DATE_FORMAT(date_of_birth, '%m-%d') as dob"],
	)
	filtered_birthday_cards = []
	current_date = from_date
	while current_date <= to_date:
		for card in birthday_cards:
			if card.dob == current_date.strftime("%m-%d"):
				filtered_birthday_cards.append((card.name, current_date.year))
		current_date += timedelta(days=1)

	return print_birthday_card(filtered_birthday_cards)


def get_birthday_card_data(birthday_card, year):
	"""
	Get the data for a birthday card.

	Args:
	    birthday_card (str): The name of the birthday card.
	    year (int): The year of the birthday.

	Returns:
	    dict: A dictionary containing the birthday card data
	"""
	birthday_card = frappe.get_doc("Birthday Card", birthday_card)
	dob = frappe.get_value("Student", birthday_card.student, "date_of_birth")
	program_name = frappe.get_value("Program", birthday_card.program, "program_name")
	division_name = frappe.get_value("Student Group", birthday_card.student_group, "student_group_name")
	student_name = frappe.get_value("Student", birthday_card.student, "student_name")
	has_traits = any(trait.description for trait in birthday_card.traits)
	age = year - dob.year
	return {
		"has_traits": has_traits,
		"traits": birthday_card.traits,
		"student_name": student_name,
		"special_day": dob.strftime("%d-%m") + "-" + str(year),
		"age": abs(age),
		"program_name": program_name,
		"division_name": division_name,
	}


@frappe.whitelist()
def create_birthday_card(program_enrollments):
	frappe.enqueue(create_birthday_card_async, program_enrollments=program_enrollments)


def create_birthday_card_async(program_enrollments):
	"""
	Create birthday cards for all the students in the selected program enrollments.
	This function is designed to run asynchronously.

	Args:
	    program_enrollments (list): A list of program enrollments.

	"""
	program_enrollments = frappe.parse_json(program_enrollments)
	existing_cards = frappe.get_all(
		"Birthday Card",
		filters={"program_enrollment": ["in", program_enrollments]},
		pluck="program_enrollment",
	)
	for program_enrollment in program_enrollments:
		try:
			if program_enrollment not in existing_cards:
				new_card = frappe.new_doc("Birthday Card")
				new_card.program_enrollment = program_enrollment
				new_card.insert(ignore_permissions=True)
		except:
			frappe.log_error("Create Birthday Card Error", frappe.get_traceback())
