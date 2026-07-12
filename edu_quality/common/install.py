import frappe
from edu_quality.edu_quality.overrides.company import create_account_head, ACCOUNT_HEADS

def after_install():
    create_default_roles()
    companies = frappe.get_all("Company", pluck="name")
    for company in companies:
        for account_head in ACCOUNT_HEADS:
            create_account_head(
                account_head["account_name"],
                account_head["parent_account_name"],
                company,
            )


def create_default_roles():
    """Ensure app-specific roles referenced in permissions/customizations exist."""
    for role_name in ("School Admin",):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc(
                {"doctype": "Role", "role_name": role_name, "desk_access": 1}
            ).insert(ignore_permissions=True)