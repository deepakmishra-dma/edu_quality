# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from edu_quality.common.utils.auth import set_user_permissions

class EventParticipant(Document):
    @frappe.whitelist()
    def get_participant_details(self):
        return frappe.json.loads(self.data)
    
    def after_insert(self):
        self.form_hash = frappe.generate_hash(self.name, length=20)
        self.save(ignore_permissions=True)
        guardian = frappe.get_all(
            "Student Guardian", {"parent": self.student}, pluck="guardian"
        )
        users = frappe.get_all("Guardian", {"name": ("in", guardian)}, pluck="user")
        for user in users:
            set_user_permissions(user, self.doctype, self.name)

        # Send registration link to the student
        self.send_registration_link()


    def on_trash(self):
        user_permission = frappe.get_all(
            "User Permission", {"allow": self.doctype, "for_value": self.name}, pluck="name"
        )
        if user_permission:
            for perm in user_permission:
                frappe.delete_doc("User Permission", perm, ignore_permissions=True)

    def send_registration_link(self, email_template=None):
        # Early exit if no student is associated
        guardian = frappe.get_all("Student Guardian", {"parent": self.student}, pluck="guardian")
        if not guardian:
            return
    
        emails = frappe.get_all("Guardian", {"name": ("in", guardian)}, pluck="email_address")
        # Early exit if no emails are found
        if not emails:
            return
    
        # Get web form URL
        web_form = frappe.get_value("Event", self.event, "web_form")
        if web_form:
            route = frappe.get_value("Web Form", web_form, "route")
        else:
            route = "event-registration"

        form_url = f"{frappe.utils.get_url()}/get-web-form?hash={self.form_hash}&redirect_to={route}"
    
        # Determine the email template to use
        if not email_template:
            email_template = frappe.get_value("Event Detail", self.event_detail, "registration_email_template")
    
        # Build context
        context = frappe.get_doc("Event Detail", self.event_detail).as_dict()
        context.update({"form_url": form_url, **self.as_dict()})
    
        # Determine subject and message
        if email_template:
            subject = frappe.render_template(frappe.get_value("Email Template", email_template, "subject"), context)
            message = frappe.render_template(frappe.get_value("Email Template", email_template, "response"), context)
        else:
            subject = f"Registration for {self.event}"
            message = f"Please click on the following link to complete your registration: <a href='{form_url}'>{form_url}</a>"
    
        # Send email
        frappe.sendmail(recipients=emails, subject=subject, message=message)

    def on_submit(self):
        if self.payment_required:
            if self.outstanding_amount < 0:
                self.outstanding_amount = 0
            if not self.paid or self.outstanding_amount > 0:
                frappe.throw("Payment is pending")
        if not frappe.db.exists(
            "Student Data", {"student": self.student, "parent": self.event_detail}
        ):
            participant = frappe.new_doc("Student Data")
            participant.student = self.student
            participant.student_name = self.student_name
            participant.refno = self.refno
            participant.event_participant_link = self.name
            participant.parent = self.event_detail
            participant.parenttype = "Event Detail"
            participant.parentfield = "participating_students"
            participant.save(ignore_permissions=True)

    def validate_payment(self, data=None):
        if data:
            amount = data.get("amount")
            self.payment_required = self.paid = 1
            if self.outstanding_amount > 0:
                self.outstanding_amount -= amount
            else:
                self.outstanding_amount = 0
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


@frappe.whitelist()
def get_data(**kwargs):
    data = {}

    # Fetch event detail data if provided
    event_detail = kwargs.get("event_detail")
    if event_detail:
        event_data = frappe.get_value(
            "Event Detail", event_detail, ["event", "event_starts_on", "school"], as_dict=True
        )
        if event_data:
            data.update(event_data)

    # Fetch student data if reference number is provided
    refno = kwargs.get("refno")
    if refno:
        # Build filters dictionary
        filters = {"reference_number": refno}
        school = kwargs.get("school")
        if school:
            filters["school"] = school
        
        # Check if the user has access to the student data
        student = frappe.get_value(
            "Student", filters,
            ["name", "student_name", "program"],
            as_dict=True,
        )
        if student:
            if frappe.has_permission("Student", "read", student.name):
                data.update(student)
            else:
                frappe.throw(_("You do not have permission to access this student's data"))

    return data
