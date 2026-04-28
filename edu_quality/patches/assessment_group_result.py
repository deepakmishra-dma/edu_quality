import frappe
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from frappe.utils import get_url


def execute():
    site_url = get_url()

    if "uat" in site_url or "test" in site_url:
        return

    all_group_results = frappe.db.get_all(
        "Assessment Group Result",
        {"academic_year": current_academic_year()},
        pluck="name",
    )

    event_participants = frappe.qb.DocType("Event Participants")
  
    event_participants_query = (
        frappe.qb.from_(event_participants)
        .select(event_participants.parent)
        .where(
            (event_participants.reference_doctype
            == "Assessment Group Result")
            & (event_participants.reference_docname.isin(all_group_results))
        )
    ).run(as_dict=True)
    all_events = [
        event_participant.parent for event_participant in event_participants_query
    ]
    for event in all_events:
        event_detail = frappe.db.get_value("Event Detail", {"event": event}, "name")
        frappe.delete_doc("Event Detail", event_detail)

    for event_participant in event_participants_query:
        frappe.delete_doc("Event", event_participant.parent)

    for group_result in all_group_results:
        assessment_group_result = frappe.get_doc(
            "Assessment Group Result", group_result
        )
        if assessment_group_result.docstatus == 1:
            assessment_group_result.docstatus = 2
            assessment_group_result.save(ignore_permissions=True)
        assessment_group_result.delete()
