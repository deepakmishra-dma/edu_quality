import frappe
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.api.print_id_card import generate_permanent_id_cards

frappe.utils.logger.set_log_level("DEBUG")
patch_logger = frappe.logger("Create ID Card Div")


def execute():
    try:
        schools = frappe.db.get_all("School", fields=["name"])
        academic_year = current_academic_year()
        for school in schools:
            all_divisions = (
                frappe.get_all(
                    "Student Group",
                    filters={
                        "custom_school": school.get("name"),
                        "academic_year": academic_year,
                    },
                )
                or []
            )
            divisions = [i.get("name") for i in all_divisions]
            all_enrollments = frappe.get_all(
                "Program Enrollment",
                filters=[["student_group", "in", divisions], ["docstatus", "=", 1]],
                fields=["name", "student_group"],
            )
            division_wise_enrollments = generate_hash(all_enrollments)

            for div, enrollments in division_wise_enrollments.items():
                patch_logger.info(
                    f"Starting generation of permanent id cards for {div} {enrollments}"
                )
                output = generate_permanent_id_cards(enrollments)

                patch_logger.info(
                    f"generated permanent id cards for {div} {enrollments} with output {output}"
                )
            #     break
            # break

    except Exception as e:
        frappe.logger("Create ID Card Div").exception(e)


def generate_hash(data):
    hashmap = {}
    for i in data:
        enrollment = i.get("name")
        division = i.get("student_group")
        if division not in hashmap:
            hashmap[division] = [enrollment]
        else:
            hashmap[division].append(enrollment)
    return hashmap
