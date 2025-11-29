import frappe
from education.education.doctype.assessment_group.assessment_group import (
    AssessmentGroup,
)
from edu_quality.public.py.utils import extract_year_from_academic_year_name
import csv
import requests
from io import StringIO
from functools import reduce


class CustomAssessmentGroup(AssessmentGroup):
    def autoname(self):
        short_acad_year = extract_year_from_academic_year_name(
            self.custom_academic_year
        )
        program = frappe.get_doc("Program", self.get("custom_program"))
        class_type = frappe.get_doc("Class Type", program.get("program_name"))
        school_pref = frappe.db.get_value("School", self.custom_school, "prefix")
        self.name = f"{self.assessment_group_name} {short_acad_year} - {school_pref}{class_type.get('short_code')}"

    # def before_validate(self):
    #     if frappe.db.exists(
    #         "Assessment Group",
    #         {
    #             "custom_order": self.custom_order,
    #             "custom_academic_year": self.custom_academic_year,
    #             "name": ["!=", self.name],
    #         },
    #     ):
    #         frappe.throw(f"Order {self.custom_order} for the class already exists")


# edu_quality.edu_quality.overrides.assessment_group.import_assessment_group
@frappe.whitelist()
def import_assessment_group(url):
    try:
        origin = frappe.request.headers.get("Origin")
        full_url = origin + url
        response = requests.get(full_url)
        response.raise_for_status()
        return import_assess_group_csv_in_bg(response.text)

    except Exception as e:
        print(e, "except")
        frappe.log_error(f"Error importing Exam Config: {str(e)}", "Exam Config Import")
        return {"status": "failed", "message": str(e)}
    finally:
        # Disconnect database connection
        print("db closed")
        # frappe.db.close()


def gen_bulk_rows(csv_reader):
    bulk_rows = []
    for idx, row in enumerate(csv_reader, start=1):
        name = row[0]
        if name:
            bulk_rows.append([row])

        else:
            bulk_rows[-1].append(row)
    return bulk_rows


def import_assess_group_csv_in_bg(csv_content):
    errors = []
    try:
        csv_reader = csv.reader(StringIO(csv_content))
        total_rows = sum(1 for _ in csv_reader) - 1  # Excluding header row
        csv_reader = csv.reader(StringIO(csv_content))
        headers = next(csv_reader)  # Skip header row
        bulk_rows = gen_bulk_rows(csv_reader)
        errors = insert_groups_into_db(bulk_rows, headers, total_rows)

        if errors:
            frappe.db.rollback()
            error_message = "Error importing Exam Config background:<br>"
            error_message += "<table>"
            error_message += "<tr><th>Row No</th><th>Error Message</th></tr>"
            for err in errors:
                error_message += f"<tr><td>{err[0]}</td><td>{err[1]}</td></tr>"
            error_message += "</table>"
            frappe.log_error("Error importing assessment groups", str(errors))
            return {"status": "failed", "message": error_message}
        frappe.db.commit()
        return {"status": "success", "message": ("Exam Config imported successfully")}
    except Exception as e:
        frappe.log_error(
            message=f"Error importing Exam Config background: {str(frappe.get_traceback())}",
            title="Exam Config Import Background",
        )
        return {"status": "failed", "message": str(e)}


def insert_groups_into_db(bulk_data, headers, total_rows):
    current_group = None
    errors = []
    try:
        for index, parent_row in enumerate(bulk_data, start=1):
            try:
                is_composite_flag = 0
                program_flag = None
                current_divs = []
                for idx, row in enumerate(parent_row, start=1):
                    try:
                        (
                            name,
                            school,
                            program,
                            div,
                            order,
                            publish_to_app,
                            printable,
                            calculate_ranks,
                            show_in_app,
                            is_composite_exam,
                            is_final_exam,
                            is_final_photo_req,
                            acad_year,
                            process_pass_or_fail,
                            passing_percentage,
                            report_print_conf,
                            remarks_template_id,
                            composite_exam_id,
                            composite_exam_avg,
                            config_subject_type,
                            config_subject_name,
                            config_subject_textbook_used,
                            config_subject_allow_reval,
                            marking_mode,
                            grading_scale,
                        ) = row[:25]

                        if name:
                            program_flag = None
                            is_composite_flag = None
                            current_divs = div.split(",")
                            local_divs = frappe.db.get_all(
                                "Student Group",
                                filters={
                                    "academic_year": acad_year,
                                    "student_group_name": [
                                        "in",
                                        current_divs or [None],
                                    ],
                                    "program": program,
                                    "custom_school": school,
                                },
                            )
                            current_divs = [i.get("name") for i in local_divs]
                            current_group = frappe.new_doc("Assessment Group")
                            current_group.parent_assessment_group = (
                                "All Assessment Groups"
                            )
                            current_group.assessment_group_name = name
                            current_group.custom_school = school
                            current_group.custom_program = program
                            current_group.custom_academic_year = acad_year
                            current_group.custom_print_configuration = report_print_conf
                            current_group.custom_order = order
                            current_group.custom_final_exam = is_final_exam
                            current_group.custom_is_printable = printable
                            current_group.custom_calculate_ranks = calculate_ranks
                            current_group.custom_show_in_app = show_in_app
                            current_group.custom_is_composite = is_composite_exam
                            current_group.custom_publish_to_app = publish_to_app
                            current_group.custom_is_final_exam_class_photo_required = (
                                is_final_photo_req
                            )
                            current_group.custom_process_passing = (
                                process_pass_or_fail or 0
                            )
                            current_group.custom_passing_percentage = (
                                passing_percentage or 0
                            )
                            current_group.save(ignore_permissions=True)
                            is_composite_flag = int(is_composite_exam)
                            program_flag = program

                        if is_composite_flag:
                            current_group.custom_is_composite = 1
                            comp_doc = frappe.new_doc("Composite Exam")
                            comp_doc.assesment_group = composite_exam_id
                            comp_doc.parent = current_group.name
                            comp_doc.parenttype = "Assessment Group"
                            comp_doc.parentfield = "custom_composite_exams"
                            comp_doc.save(ignore_permissions=True)

                        if not is_composite_flag:
                            subj_map = generate_config_hash(row, headers)

                            insert_assessment_plan(
                                current_group,
                                current_divs,
                                config_subject_name,
                                config_subject_type,
                                config_subject_textbook_used,
                                config_subject_allow_reval,
                                program_flag,
                                subj_map,
                                grading_scale,
                                marking_mode,
                            )
                        progress = idx * 100 // total_rows
                        frappe.realtime.publish_progress(
                            progress,
                            title="Import Exams",
                            description=f"{idx}/{total_rows} rows processed",
                        )

                    except Exception as e:
                        err = [idx, str(e)]
                        errors.append(err)

            except Exception as e:
                err = [idx, str(e)]
                errors.append(err)
        return errors
    except Exception as e:
        err = [f"Group {index}", str(e)]
        errors.append(err)
        return errors


def generate_config_hash(row, headers):
    hashmap = {}
    for idx in range(len(headers)):
        header = headers[idx]
        if ("_exam_type" in header) and row[idx]:
            hashmap[header] = {
                "assessment_criteria": row[idx],
                "maximum_score": row[idx + 1] or 0,
                "custom_scale": row[idx + 2] or 1,
                "custom_include_in_ranking": int(row[idx + 3] or 1),
            }
    return hashmap


def insert_assessment_plan(
    current_group,
    divs,
    subject,
    config_subject_type,
    config_subject_textbook_used,
    config_subject_allow_reval,
    program,
    subj_map,
    grading_scale,
    marking_mode,
):
    criterias = [subj_map[i] for i in subj_map]

    for div in divs:
        name = frappe.db.get_value(
            "Assessment Plan",
            {
                "student_group": div,
                "program": program,
                "course": subject,
                "assessment_group": current_group.name,
                "custom_type": config_subject_type,
                "custom_textbook": ["in", ["All", config_subject_textbook_used]],
            },
            "name",
        )
        if not name:
            assess_plan = frappe.new_doc("Assessment Plan")
            assess_plan.assessment_group = current_group.name
            assess_plan.student_group = div
            assess_plan.program = program
            assess_plan.custom_scoring_type = marking_mode
            assess_plan.custom_type = config_subject_type
            assess_plan.custom_textbook = (
                "ALL"
                if str(config_subject_textbook_used).lower() == "all"
                else config_subject_textbook_used
            )
            assess_plan.course = subject
            assess_plan.maximum_assessment_score = sum_criterias(criterias)
            assess_plan.grading_scale = grading_scale
            assess_plan.custom_allow_revaluation = config_subject_allow_reval
            for criteria in criterias:
                check_and_create_assessment_criteria(criteria)
                assess_plan.append(
                    "assessment_criteria",
                    {
                        **criteria,
                        "maximum_score": int(criteria.get("maximum_score")),
                        "custom_scale": float(criteria.get("custom_scale")),
                    },
                )

            assess_plan.save(ignore_permissions=True)
        else:
            for criteria in criterias:
                assess_plan_cr = frappe.new_doc("Assessment Plan Criteria")
                assess_plan_cr.parent = name
                assess_plan_cr.parenttype = "Assessment Plan"
                assess_plan_cr.parentfield = "assessment_criteria"
                check_and_create_assessment_criteria(criteria)
                assess_plan_cr.assessment_criteria = criteria.get("assessment_criteria")
                assess_plan_cr.maximum_score = int(criteria.get("maximum_score"))
                assess_plan_cr.custom_scale = float(criteria.get("custom_scale"))
                assess_plan_cr.custom_include_in_ranking = int(
                    criteria.get("custom_include_in_ranking")
                )
                assess_plan_cr.save()


def check_and_create_assessment_criteria(criteria):
    if not frappe.db.exists("Assessment Criteria", criteria.get("assessment_criteria")):
        assess_cr = frappe.new_doc("Assessment Criteria")
        assess_cr.assessment_criteria = criteria.get("assessment_criteria")
        assess_cr.save()


def sum_criterias(criterias):
    print(criterias)
    return reduce(lambda x, y: x + float(y.get("maximum_score")), criterias, 0)
