import frappe
from frappe.auth import LoginManager


@frappe.whitelist(allow_guest=True)
def get_web_form(**kwargs):
	"""
	Get Web Form URL for the given doctype and hash
	Args:
	    doctype (str): Doctype to get the URL for
	    hash (str): Hash of the document
	    redirect_to (str): Redirect URL to append to the URL
	"""
	_hash = kwargs.get("hash")
	redirect_to = kwargs.get("redirect_to")
	frappe.response["success"] = False
	if not _hash or not redirect_to:
		frappe.response["message"] = "Hash or Redirect is missing, please contact the administrator"
		return
	doctype = frappe.get_value("Web Form", {"route": redirect_to}, "doc_type")
	docname = frappe.get_value(doctype, {"form_hash": _hash})
	if docname:
		user = frappe.get_value("User Permission", {"allow": doctype, "for_value": docname}, ["user"])
		if user:
			login_manager = LoginManager()
			login_manager.login_as(user)
			frappe.response["success"] = True
			frappe.response["message"] = frappe.utils.get_url() + f"/{redirect_to}/{docname}/edit"


def set_user_permissions(user, doctype, value):
	"""
	Set User Permissions for the given user, doctype and value
	Args:
	    user (str): User to set permission for
	    doctype (str): Doctype to set permission for
	    value (str): Value to set permission for
	"""
	if not user:
		return
	if not frappe.db.exists("User Permission", {"user": user, "allow": doctype, "for_value": value}):
		perm = frappe.new_doc("User Permission")
		perm.user = user
		perm.allow = doctype
		perm.for_value = value
		perm.insert(ignore_permissions=True)


def remove_user_permissions(user, doctype, value=None):
	"""
	Remove user permissions for the given user, doctype and value
	"""
	filters = {"user": user, "allow": doctype}
	if value:
		filters["for_value"] = value
	user_permissions = frappe.get_all("User Permission", filters=filters)
	for up in user_permissions:
		frappe.delete_doc("User Permission", up.name, ignore_permissions=True)
