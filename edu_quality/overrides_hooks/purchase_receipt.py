from datetime import datetime
import pytz
import frappe


def before_save(self, method=None):
    old_doc = self.get_doc_before_save()
    if (
        old_doc
        and old_doc.workflow_state != "Received"
        and self.workflow_state == "Received"
    ):
        id_card_items = [item for item in self.items if item.item_code == "ID Card"]

        if not len(id_card_items):
            return
        for item in id_card_items:
            if not frappe.db.get_value(
                "Purchase Order", item.purchase_order, "custom_is_id_card"
            ):
                continue

            reference_docname = frappe.db.get_value(
                "Purchase Order",
                item.purchase_order,
                "custom_reference_docname",
            )
            id_card_doc = frappe.get_doc(
                "Permanent Id Card", reference_docname, ignore_permissions=True
            )
            for card in id_card_doc.id_cards:
                frappe.db.set_value(
                    "Student ID Card",
                    card.id_card,
                    "status",
                    "RECEIVED BY SCHOOL",
                )
                frappe.get_doc(
                    {
                        "doctype": "ID Card Event",
                        "parenttype": "Student ID Card",
                        "timestamp": frappe.utils.now(),
                        "parentfield": "events",
                        "status": "SENT TO PRINT",
                        "user": frappe.session.user,
                        "parent": card.id_card,
                    }
                ).insert(ignore_permissions=True)

        utc_now = datetime.now(pytz.UTC)
        ist_now = utc_now.astimezone(pytz.timezone("Asia/Kolkata")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        self.custom_receiving_date = ist_now
        self.custom_received_by = frappe.session.user
