import frappe
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from frappe.utils import get_url
from edu_quality.api.exam_result import process_result


def set_program_enrollment_image():
    academic_year = current_academic_year()
    student_qb = frappe.qb.DocType("Student")
    program_qb = frappe.qb.DocType("Program Enrollment")
    data = (
        frappe.qb.from_(student_qb)
        .inner_join(program_qb)
        .on(student_qb.name == program_qb.student)
        .where(
            student_qb.image.isnull()
            & program_qb.image.isnotnull()
            & (program_qb.academic_year == academic_year)
            & (program_qb.docstatus == 1)
        )
        .select(program_qb.image, student_qb.name, student_qb.image.as_("stud_img"))
        .run(as_dict=True)
    )
    for student in data:
        if not student.stud_img:
            frappe.db.set_value("Student", student.name, "image", student.image)


def execute():
    try:
        site_url = get_url()

        if "uat" in site_url or "test" in site_url:
            return

        set_program_enrollment_image()

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
                (event_participants.reference_doctype == "Assessment Group Result")
                & (
                    event_participants.reference_docname.isin(
                        all_group_results or [None]
                    )
                )
            )
        ).run(as_dict=True)
        all_events = [
            event_participant.parent for event_participant in event_participants_query
        ]
        # get all assessment results that are submitted and assessment group field from their make a set out of it
        assessment_group_names = frappe.db.get_all(
            "Assessment Group Result",
            {"academic_year": current_academic_year()},
            pluck="assessment_group",
        ) or frappe.db.get_all(
            "Assessment Result",
            {"academic_year": current_academic_year(), "docstatus": 1},
            pluck="assessment_group",
        )

        assessment_group_names = set(assessment_group_names)

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

        for assessment_group_name in assessment_group_names:
            assess_group_doc = frappe.get_doc("Assessment Group", assessment_group_name)
            try:
                process_result(
                    assess_group_doc.name,
                    current_academic_year(),
                    assess_group_doc.custom_program,
                    None,
                    "",
                    create_toppers_only=True,
                )
            except:
                frappe.log_error(
                    f"Skipping assessment group {assessment_group_name}",
                    frappe.get_traceback(),
                )
                continue

    except Exception as e:
        frappe.log_error("Error while running patch", frappe.get_traceback())
        raise e
