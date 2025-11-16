# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EventParticipant(Document):
    @frappe.whitelist()
    def get_participant_details(self):
        return frappe.json.loads(self.data)

    def on_submit(self):
        if self.outstanding_amount < 0:
            self.outstanding_amount = 0
        if not self.paid or self.outstanding_amount != 0:
            frappe.throw("Payment is pending")
        if not frappe.db.exists(
            "Student Data", {"student": self.student, "parent": self.event_detail}
        ):
            participant = frappe.new_doc("Student Data")
            participant.student = self.student
            participant.student_name = self.student_name
            participant.refno = self.refno
            participant.parent = self.event_detail
            participant.parenttype = "Event Detail"
            participant.parentfield = "participating_students"
            participant.save(ignore_permissions=True)

    def validate_payment(self, data=None):
        if data:
            amount = data.get("amount")
            self.paid = 1
            self.outstanding_amount -= amount
            self.paid_amount = amount
            self.save(ignore_permissions=True)
            self.submit()
            return {"status": "success", "message": "Payment Successful"}
        else:
            return {"status": "error", "message": "Payment data not found"}


@frappe.whitelist()
def export_participant_data(event_detail):
    data = []
    participant = frappe.get_all(
        "Event Participant",
        filters={"event_detail": event_detail},
        fields=["name", "data"],
    )
    for p in participant:
        data.append(frappe.json.loads(p.data))
    return data
