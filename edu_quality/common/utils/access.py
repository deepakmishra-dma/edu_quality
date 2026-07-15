"""Authorization helpers for guardian/staff-facing endpoints.

These centralize the "who may see/act on this student" checks so that
whitelisted endpoints do not have to re-implement (or forget) ownership
validation.
"""

import frappe
from frappe import _

# Roles that may act on any student's records (school staff).
STAFF_ROLES = {"Administrator", "System Manager", "School Admin", "Instructor"}
# Roles allowed to perform sensitive financial/administrative writes.
ADMIN_ROLES = {"Administrator", "System Manager", "School Admin"}


def session_guardian():
	"""Return the Guardian name linked to the current session user, or None."""
	user = frappe.session.user
	if not user or user == "Guest":
		return None
	return frappe.db.get_value("Guardian", {"user": user}, "name")


def _has_role(roles):
	user = frappe.session.user
	if not user or user == "Guest":
		return False
	return bool(set(frappe.get_roles(user)) & roles)


def is_staff():
	return _has_role(STAFF_ROLES)


def guardian_owns_student(student):
	guardian = session_guardian()
	if not guardian or not student:
		return False
	return bool(
		frappe.db.exists(
			"Student Guardian",
			{"guardian": guardian, "parent": student, "parenttype": "Student"},
		)
	)


def assert_student_access(student):
	"""Permit school staff, or a guardian linked to `student`. Raise otherwise."""
	if is_staff() or guardian_owns_student(student):
		return
	frappe.throw(_("You are not permitted to access this record."), frappe.PermissionError)


def assert_staff():
	"""Restrict to school staff (any staff role)."""
	if not is_staff():
		frappe.throw(_("You are not permitted to access this resource."), frappe.PermissionError)


def assert_admin():
	"""Restrict to school-administration roles."""
	if not _has_role(ADMIN_ROLES):
		frappe.throw(_("You are not permitted to perform this action."), frappe.PermissionError)
