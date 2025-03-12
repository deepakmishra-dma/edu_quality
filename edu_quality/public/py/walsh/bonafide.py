import frappe
from nextai.funnel.custom_trigger import trigger_event


@frappe.whitelist(allow_guest=True)
def send_bonafide(student_id):
    # from nextai.funnel.custom_trigger import trigger_event
    student = frappe.get_doc("Student", student_id)
    trigger_event(doc=student, event_name="bonafide_certificate")
    
    