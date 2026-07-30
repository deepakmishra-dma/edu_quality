# Copyright (c) 2026, Walnut and contributors
# For license information, please see license.txt

"""Tests for the Admissions MIS dashboard API.

Fixtures use far-future academic years and a dedicated prefix so they cannot
collide with, or be affected by, whatever data a site already holds.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from edu_quality.api import admissions_dashboard as dashboard

PREFIX = "_TestAdmDash"
CURRENT_YEAR = "2100-2101"
PREVIOUS_YEAR = "2099-2100"

ALPHA = "%s Alpha School" % PREFIX
BETA = "%s Beta School" % PREFIX
ALPHA_LOCATION = "%s Alphaville" % PREFIX
BETA_LOCATION = "%s Betatown" % PREFIX

RESTRICTED_USER = "_test_adm_dash_restricted@example.com"


def _insert(doc):
	"""Insert a fixture through the normal document lifecycle."""
	doc = frappe.get_doc(doc)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_links = True
	doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
	return doc


def _db_insert(doc, name, docstatus=0):
	"""Write a fixture row straight to the database, skipping controllers.

	These tests cover the reporting aggregates, not the lifecycle of the
	doctypes they read. Program Enrollment in particular runs a before_insert
	hook that expects a full Student record, which would drag Student's schema
	(and whatever child tables a given site has bolted onto it) into every test
	here. Writing the row directly keeps the fixtures portable and fast.

	Admission Target is deliberately *not* created this way -- its validation is
	itself under test, so it goes through the normal insert path.
	"""
	doc = frappe.get_doc(doc)
	doc.name = name
	doc.docstatus = docstatus
	doc.db_insert()
	return doc


class TestAdmissionsDashboard(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Clear anything a previously interrupted run left behind, so the
		# fixtures below always start from a known state.
		cls._cleanup()
		cls._make_academic_years()
		cls._make_schools_and_programs()
		cls._make_enrolments()
		cls._make_applicants()
		cls._make_leads()
		cls._make_student_groups()
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		cls._cleanup()
		super().tearDownClass()

	@classmethod
	def _cleanup(cls):
		# Rows we named ourselves. Removed with a raw delete to mirror how they
		# were written -- submitted documents cannot go through delete_doc.
		for doctype in ("Student Group", "Lead", "Student Applicant", "Program Enrollment"):
			frappe.db.delete(doctype, {"name": ("like", "%s%%" % PREFIX)})

		# Programs are autonamed, so they are found via their school instead.
		for name in frappe.get_all(
			"Program", filters={"school": ("in", [ALPHA, BETA])}, pluck="name"
		):
			for target in frappe.get_all("Admission Target", filters={"program": name}, pluck="name"):
				frappe.delete_doc("Admission Target", target, force=True, ignore_permissions=True)
			frappe.delete_doc("Program", name, force=True, ignore_permissions=True)

		for name in frappe.get_all(
			"User Permission", filters={"user": RESTRICTED_USER}, pluck="name"
		):
			frappe.delete_doc("User Permission", name, force=True, ignore_permissions=True)

		for doctype, names in (
			("School", [ALPHA, BETA]),
			("Academic Year", [CURRENT_YEAR, PREVIOUS_YEAR]),
			("User", [RESTRICTED_USER]),
		):
			for name in names:
				if frappe.db.exists(doctype, name):
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

		frappe.db.commit()

	# ---------------------------------------------------------------- fixtures

	@classmethod
	def _make_academic_years(cls):
		for name, start, end in (
			(PREVIOUS_YEAR, "2099-04-01", "2100-03-31"),
			(CURRENT_YEAR, "2100-04-01", "2101-03-31"),
		):
			if not frappe.db.exists("Academic Year", name):
				_insert(
					{
						"doctype": "Academic Year",
						"academic_year_name": name,
						"year_start_date": start,
						"year_end_date": end,
					}
				)

	@classmethod
	def _make_schools_and_programs(cls):
		for school, location in ((ALPHA, ALPHA_LOCATION), (BETA, BETA_LOCATION)):
			if not frappe.db.exists("School", school):
				_insert({"doctype": "School", "school": school, "location": location})

		# Nursery feeds into 1, so the chain decides the class order.
		cls.programs = {}
		for school in (ALPHA, BETA):
			nursery = cls._program(school, "Nursery")
			first = cls._program(school, "1", previous_class=nursery)
			cls.programs[school] = {"Nursery": nursery, "1": first}

	@classmethod
	def _program(cls, school, program_name, previous_class=None):
		"""Create a Program and return the name Frappe actually gave it.

		Program autonames itself from its fields, so the id cannot be assumed --
		and every program-keyed figure (capacity, targets, class splits) breaks
		silently if it is guessed wrong.
		"""
		existing = frappe.get_all(
			"Program", filters={"program_name": program_name, "school": school}, pluck="name"
		)
		if existing:
			return existing[0]

		doc = _insert(
			{
				"doctype": "Program",
				"program_name": program_name,
				"program_abbreviation": "%s %s %s" % (PREFIX, program_name, school),
				"school": school,
				"previous_class": previous_class,
			}
		)
		return doc.name

	@classmethod
	def _student(cls, index):
		"""A synthetic student identifier.

		Strength is counted by distinct ``student`` value, so the aggregates only
		need the identifier -- not a Student record. Skipping the record keeps
		these tests independent of Student's own schema, which on some sites
		pulls in child tables whose modules no longer exist.
		"""
		return "%s Student %d" % (PREFIX, index)

	@classmethod
	def _make_enrolments(cls):
		"""Alpha: 2 continuing + 1 new. Beta: 1. One Alpha pupil does not continue."""
		plan = [
			# (student index, school, class, year)
			(1, ALPHA, "Nursery", PREVIOUS_YEAR),
			(2, ALPHA, "Nursery", PREVIOUS_YEAR),
			(3, ALPHA, "Nursery", PREVIOUS_YEAR),  # leaves before CURRENT_YEAR
			(1, ALPHA, "1", CURRENT_YEAR),
			(2, ALPHA, "1", CURRENT_YEAR),
			(4, ALPHA, "Nursery", CURRENT_YEAR),
			(5, BETA, "Nursery", CURRENT_YEAR),
		]
		for position, (index, school, klass, year) in enumerate(plan):
			_db_insert(
				{
					"doctype": "Program Enrollment",
					"student": cls._student(index),
					"student_name": cls._student(index),
					"program": cls.programs[school][klass],
					"academic_year": year,
					"custom_school": school,
					"custom_status": "Current student",
					"enrollment_date": "2100-04-01",
				},
				name="%s Enrolment %d" % (PREFIX, position),
				docstatus=1,
			)

	@classmethod
	def _make_applicants(cls):
		"""Two admitted at Alpha, one at Beta, plus one merely Applied at Alpha."""
		plan = [
			(ALPHA, "Nursery", "Admitted", "2100-05-01"),
			(ALPHA, "1", "Admitted", "2100-06-01"),
			(BETA, "Nursery", "Admitted", "2100-05-01"),
			(ALPHA, "Nursery", "Applied", "2100-05-01"),
		]
		for position, (school, klass, status, date) in enumerate(plan):
			_db_insert(
				{
					"doctype": "Student Applicant",
					"first_name": "%s Applicant" % PREFIX,
					"academic_year": CURRENT_YEAR,
					"school": school,
					"program": cls.programs[school][klass],
					"application_status": status,
					"application_date": date,
				},
				name="%s Applicant %d" % (PREFIX, position),
			)

	@classmethod
	def _make_leads(cls):
		"""Four Alpha enquiries (one waiting-list) and two Beta enquiries."""
		plan = [
			(ALPHA, "Nursery", "Fresh"),
			(ALPHA, "Nursery", "Fresh"),
			(ALPHA, "1", "Fresh"),
			(ALPHA, "1", "Waiting list"),
			(BETA, "Nursery", "Fresh"),
			(BETA, "Nursery", "Waiting list"),
		]
		for position, (school, klass, status) in enumerate(plan):
			_db_insert(
				{
					"doctype": "Lead",
					"lead_name": "%s Lead" % PREFIX,
					"first_name": "%s Lead" % PREFIX,
					"academic_year": CURRENT_YEAR,
					"center": school,
					"class": cls.programs[school][klass],
					"status": status,
				},
				name="%s Lead %d" % (PREFIX, position),
			)

	@classmethod
	def _make_student_groups(cls):
		"""One division of 30 seats per class, per school."""
		for school in (ALPHA, BETA):
			for klass in ("Nursery", "1"):
				name = "%s Group %s %s" % (PREFIX, school, klass)
				_db_insert(
					{
						"doctype": "Student Group",
						"student_group_name": name,
						"group_based_on": "Batch",
						"academic_year": CURRENT_YEAR,
						"program": cls.programs[school][klass],
						"max_strength": 30,
					},
					name=name,
				)

	# ------------------------------------------------------------------ helpers

	def _row(self, rows, location):
		return next(row for row in rows if row["location"] == location)

	def _make_restricted_user(self):
		"""A user who may read the sources but is limited to the Alpha school."""
		if not frappe.db.exists("User", RESTRICTED_USER):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": RESTRICTED_USER,
					"first_name": "Restricted",
					"send_welcome_email": 0,
				}
			)
			user.flags.ignore_permissions = True
			user.insert(ignore_permissions=True)
			user.add_roles("System Manager", "Academics User")

		if not frappe.db.exists(
			"User Permission", {"user": RESTRICTED_USER, "allow": "School", "for_value": ALPHA}
		):
			_insert(
				{
					"doctype": "User Permission",
					"user": RESTRICTED_USER,
					"allow": "School",
					"for_value": ALPHA,
				}
			)
		frappe.db.commit()

	# -------------------------------------------------------- derivation logic

	def test_class_order_follows_progression_chain(self):
		"""Nursery precedes 1 because Program.previous_class says so."""
		meta = dashboard.get_dashboard_meta()
		keys = [column["key"] for column in meta["classes"]]
		self.assertIn("Nursery", keys)
		self.assertIn("1", keys)
		self.assertLess(keys.index("Nursery"), keys.index("1"))

	def test_short_labels_are_derived_not_hardcoded(self):
		self.assertEqual(dashboard._short_label("Nursery"), "Nur")
		self.assertEqual(dashboard._short_label("Junior KG"), "JK")
		self.assertEqual(dashboard._short_label("Grade 1"), "G1")
		self.assertEqual(dashboard._short_label("1"), "1")
		self.assertEqual(dashboard._short_label("10"), "10")

	def test_on_roll_statuses_exclude_off_roll_options(self):
		statuses = dashboard._on_roll_statuses()
		if statuses is None:
			self.skipTest("This site has no Program Enrollment status field")
		self.assertIn("Current student", statuses)
		self.assertNotIn("Cancelled", statuses)
		self.assertNotIn("Alumni", statuses)

	def test_percent_guards_zero_denominator(self):
		self.assertEqual(dashboard._percent(5, 0), 0.0)
		self.assertEqual(dashboard._percent(1, 4), 25.0)

	def test_previous_year_never_returns_a_later_year(self):
		"""Regression: with blank dates the old code returned the *next* year."""
		self.assertEqual(dashboard._previous_academic_year(CURRENT_YEAR), PREVIOUS_YEAR)

		# Whatever a site's other years look like, the answer is never later.
		for year in (CURRENT_YEAR, PREVIOUS_YEAR):
			resolved = dashboard._previous_academic_year(year)
			if resolved:
				self.assertLess(
					dashboard._leading_year(resolved),
					dashboard._leading_year(year),
					"previous year of %s resolved forwards to %s" % (year, resolved),
				)

	# ------------------------------------------------------- aggregate figures

	def test_strength_analysis_counts(self):
		result = dashboard.get_strength_analysis(CURRENT_YEAR)
		self.assertEqual(result["previous_academic_year"], PREVIOUS_YEAR)

		alpha = self._row(result["rows"], ALPHA_LOCATION)
		self.assertEqual(alpha["strength_current"], 3)  # students 1, 2, 4
		self.assertEqual(alpha["strength_previous"], 3)  # students 1, 2, 3
		self.assertEqual(alpha["cancelled"], 1)  # student 3 did not continue
		self.assertEqual(alpha["new_admissions"], 2)  # "Applied" is not counted
		self.assertEqual(alpha["enquiries"], 4)
		self.assertEqual(alpha["capacity"], 60)  # two divisions of 30
		self.assertEqual(alpha["added_students"], 0)

		beta = self._row(result["rows"], BETA_LOCATION)
		self.assertEqual(beta["strength_current"], 1)
		self.assertEqual(beta["new_admissions"], 1)

	def test_totals_row_sums_counts_and_recomputes_percentages(self):
		rows = dashboard.get_strength_analysis(CURRENT_YEAR)["rows"]
		total = next(row for row in rows if row.get("is_total"))
		branches = [row for row in rows if not row.get("is_total")]

		self.assertEqual(total["strength_current"], sum(r["strength_current"] for r in branches))
		self.assertEqual(total["new_admissions"], sum(r["new_admissions"] for r in branches))
		# A percentage is recomputed from the totals, never summed.
		self.assertEqual(
			total["convert_percent"],
			dashboard._percent(total["new_admissions"], total["enquiries"]),
		)

	def test_target_and_balance_blank_until_configured(self):
		alpha = self._row(dashboard.get_strength_analysis(CURRENT_YEAR)["rows"], ALPHA_LOCATION)
		self.assertIsNone(alpha["target"])
		self.assertIsNone(alpha["balance"])

		target = _insert(
			{
				"doctype": "Admission Target",
				"academic_year": CURRENT_YEAR,
				"program": self.programs[ALPHA]["Nursery"],
				"target": 10,
			}
		)
		try:
			alpha = self._row(dashboard.get_strength_analysis(CURRENT_YEAR)["rows"], ALPHA_LOCATION)
			self.assertEqual(alpha["target"], 10)
			self.assertEqual(alpha["balance"], 10 - alpha["new_admissions"])
		finally:
			frappe.delete_doc("Admission Target", target.name, force=True, ignore_permissions=True)

	def test_class_distribution_splits_admissions_by_class(self):
		result = dashboard.get_class_distribution(CURRENT_YEAR)
		alpha = self._row(result["rows"], ALPHA_LOCATION)
		self.assertEqual(alpha["admissions"]["Nursery"], 1)
		self.assertEqual(alpha["admissions"]["1"], 1)
		self.assertEqual(alpha["admissions"]["total"], 2)

	def test_branch_report_months_and_conversion(self):
		result = dashboard.get_branch_report(CURRENT_YEAR)
		alpha = next(b for b in result["branches"] if b["location"] == ALPHA_LOCATION)
		self.assertEqual(alpha["stats"]["total_admissions"], 2)
		self.assertEqual(
			alpha["stats"]["conversion_rate"],
			dashboard._percent(2, alpha["stats"]["total_enquiries"]),
		)
		self.assertEqual({m["month"] for m in alpha["months"]} & {"2100-05", "2100-06"},
			{"2100-05", "2100-06"})

	def test_admission_detail_matrix_and_waiting_list(self):
		result = dashboard.get_admission_detail(CURRENT_YEAR, ALPHA_LOCATION)
		self.assertEqual(result["location"], ALPHA_LOCATION)
		self.assertEqual(result["columns"][-1], "Total")

		by_name = {row["name"]: row["data"] for row in result["stats"]}
		self.assertEqual(by_name["Admissions"][-1], 2)
		self.assertEqual(by_name["Enquiries"][-1], 4)
		self.assertEqual(by_name["Capacity"][-1], 60)

		# One Alpha lead sits on the waiting list, and the matrix leads with a total.
		self.assertTrue(result["waiting_list"])
		self.assertEqual(result["waiting_list"][0]["name"], "Total")
		self.assertEqual(result["waiting_list"][0]["data"][-1], 1)

	# --------------------------------------------------------- filter handling

	def test_unknown_academic_year_returns_empty_rather_than_erroring(self):
		result = dashboard.get_strength_analysis("%s No Such Year" % PREFIX)
		total = next(row for row in result["rows"] if row.get("is_total"))
		self.assertEqual(total["strength_current"], 0)
		self.assertEqual(total["new_admissions"], 0)

	def test_missing_academic_year_falls_back_to_the_running_year(self):
		meta = dashboard.get_dashboard_meta()
		self.assertIn(meta["default_academic_year"], meta["academic_years"])
		self.assertEqual(
			dashboard.get_strength_analysis()["academic_year"], meta["default_academic_year"]
		)

	def test_unknown_branch_is_rejected(self):
		with self.assertRaises(frappe.PermissionError):
			dashboard.get_admission_detail(CURRENT_YEAR, "%s Nowhere" % PREFIX)

	# ------------------------------------------------------------- permissions

	def test_guest_is_refused(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				dashboard.get_dashboard_meta()
		finally:
			frappe.set_user("Administrator")

	def test_restricted_user_sees_only_their_school(self):
		"""A User Permission on School must narrow every figure, not just the list.

		The aggregates use raw SQL and frappe.get_all, neither of which applies
		User Permissions, so this is the regression test for that gap.
		"""
		self._make_restricted_user()
		frappe.set_user(RESTRICTED_USER)
		try:
			meta = dashboard.get_dashboard_meta()
			self.assertIn(ALPHA_LOCATION, meta["locations"])
			self.assertNotIn(BETA_LOCATION, meta["locations"])

			rows = dashboard.get_strength_analysis(CURRENT_YEAR)["rows"]
			locations = {row["location"] for row in rows if not row.get("is_total")}
			self.assertNotIn(BETA_LOCATION, locations)

			# Beta's pupil and applicant must not leak into the totals.
			total = next(row for row in rows if row.get("is_total"))
			self.assertEqual(total["strength_current"], 3)
			self.assertEqual(total["new_admissions"], 2)
			self.assertEqual(total["capacity"], 60)

			branches = {b["location"] for b in dashboard.get_branch_report(CURRENT_YEAR)["branches"]}
			self.assertNotIn(BETA_LOCATION, branches)

			distribution = {r["location"] for r in dashboard.get_class_distribution(CURRENT_YEAR)["rows"]}
			self.assertNotIn(BETA_LOCATION, distribution)
		finally:
			frappe.set_user("Administrator")

	def test_restricted_user_cannot_request_another_branch(self):
		self._make_restricted_user()
		frappe.set_user(RESTRICTED_USER)
		try:
			with self.assertRaises(frappe.PermissionError):
				dashboard.get_admission_detail(CURRENT_YEAR, BETA_LOCATION)
		finally:
			frappe.set_user("Administrator")


class TestAdmissionTarget(FrappeTestCase):
	def test_duplicate_target_is_rejected(self):
		year = frappe.get_all("Academic Year", pluck="name", limit=1)
		program = frappe.get_all("Program", pluck="name", limit=1)
		if not year or not program:
			self.skipTest("Site has no Academic Year or Program to target")

		first = _insert(
			{
				"doctype": "Admission Target",
				"academic_year": year[0],
				"program": program[0],
				"target": 25,
			}
		)
		try:
			duplicate = frappe.get_doc(
				{
					"doctype": "Admission Target",
					"academic_year": year[0],
					"program": program[0],
					"target": 40,
				}
			)
			with self.assertRaises(frappe.DuplicateEntryError):
				duplicate.insert(ignore_permissions=True)
		finally:
			frappe.delete_doc("Admission Target", first.name, force=True, ignore_permissions=True)

	def test_school_is_derived_from_the_program(self):
		program = frappe.get_all("Program", fields=["name", "school"], limit=1)
		year = frappe.get_all("Academic Year", pluck="name", limit=1)
		if not program or not year or not program[0].school:
			self.skipTest("Site has no Program with a school to derive from")

		target = _insert(
			{
				"doctype": "Admission Target",
				"academic_year": year[0],
				"program": program[0].name,
				"target": 5,
			}
		)
		try:
			self.assertEqual(target.school, program[0].school)
		finally:
			frappe.delete_doc("Admission Target", target.name, force=True, ignore_permissions=True)
