# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from edu_quality.edu_quality.server_scripts.student_applicant import generate_hash
from frappe.auth import LoginManager


class BirthdayCard(Document):
    def after_insert(self, method=None):
        self.form_hash = generate_hash(self.name)
        self.save(ignore_permissions=True)
        set_guardian_permissions(self)


@frappe.whitelist(allow_guest=True)
def get_birthday_form(hash):

    if frappe.db.exists("Birthday Card", {"form_hash": hash}):
        birthday_card = frappe.db.get_value(
            "Birthday Card", {"form_hash": hash}, "name"
        )
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
