import frappe 
from frappe import _, scrub
from erpnext.setup.doctype.employee.employee import Employee
from frappe.permissions import (
	add_user_permission,
	get_doc_permissions,
	has_permission,
	remove_user_permission,
)
from frappe.utils.data import cint

class customEmployee(Employee):
	def update_user_permissions(self):
		if not self.create_user_permission:
			return
		if not has_permission("User Permission", ptype="write"):
			return

		employee_user_permission_exists = frappe.db.exists(
			"User Permission", {"allow": "Employee", "for_value": self.name, "user": self.user_id}
		)

		if employee_user_permission_exists:
			return

		add_user_permission("Employee", self.name, self.user_id)
		# add_user_permission("Company", self.company, self.user_id)

	def validate_preferred_email(self):
		cwe = frappe.get_value("Google Service Account", None, "create_employee_workspace")
		if cint(cwe):
			return
		if self.is_support_staff:
			return
		if self.prefered_contact_email and not self.get(scrub(self.prefered_contact_email)):
			frappe.msgprint(_("Please enter {0}").format(self.prefered_contact_email))