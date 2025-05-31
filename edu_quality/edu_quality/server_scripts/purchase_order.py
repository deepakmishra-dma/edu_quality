import frappe
from frappe.utils import getdate


def on_submit(doc, method=None):
    try:
        doc.db_set("transaction_date", getdate())
        doc.db_set("custom_sent_by", frappe.session.user)
        doc.db_set("sent_by", frappe.session.user)
    except Exception as e:
        frappe.logger("purchase").exception(e)


def mark_id_card_sent_to_print(self, method=None):
    if (
        self.custom_is_id_card
        and self.custom_reference_doctype
        and self.custom_reference_name
    ):
        perm_id_card = frappe.get_doc(
            self.custom_reference_doctype, self.custom_reference_docname
        )
        for id_card in perm_id_card.id_cards:
            frappe.db.set_value(
                "Student ID Card", id_card.get("id_card"), "status", "SENT TO PRINT"
            )
