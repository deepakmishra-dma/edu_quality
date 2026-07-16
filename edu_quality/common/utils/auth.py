import frappe
from frappe import _
from frappe.auth import LoginManager
from frappe.utils import date_diff, now_datetime


def _throttle_magic_link():
	"""Per-IP throttle so form_hash values cannot be brute-force enumerated."""
	ip = getattr(frappe.local, "request_ip", None) or "unknown"
	cache_key = f"magic_link_attempts:{ip}"
	rs = frappe.cache()
	attempts = int(rs.get_value(cache_key) or 0)
	if attempts >= 20:
		frappe.throw(_("Too many requests. Please try again later."), frappe.ValidationError)
	rs.set_value(cache_key, attempts + 1, expires_in_sec=3600)


@frappe.whitelist(allow_guest=True)
def get_web_form(**kwargs):
	"""
	Get Web Form URL for the given doctype and hash
	Args:
	    doctype (str): Doctype to get the URL for
	    hash (str): Hash of the document
	    redirect_to (str): Redirect URL to append to the URL
	"""
	_throttle_magic_link()
	_hash = kwargs.get("hash")
	redirect_to = kwargs.get("redirect_to")
	frappe.response["success"] = False
	if not _hash or not redirect_to:
		frappe.response["message"] = "Hash or Redirect is missing, please contact the administrator"
		return
	doctype = frappe.get_value("Web Form", {"route": redirect_to}, "doc_type")
	docname, modified = frappe.db.get_value(doctype, {"form_hash": _hash}, ["name", "modified"]) or (
		None,
		None,
	)
	if docname:
		# Expire stale links so a leaked URL is not usable indefinitely.
		ttl_days = frappe.conf.get("magic_link_ttl_days", 30)
		if ttl_days and modified and date_diff(now_datetime(), modified) > int(ttl_days):
			frappe.response["message"] = "This link has expired. Please request a new one."
			return
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
