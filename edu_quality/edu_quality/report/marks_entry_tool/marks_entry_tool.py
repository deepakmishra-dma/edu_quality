# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt


import frappe
from edu_quality.public.py.utils import to_snake_case
import json
from frappe.utils import flt
from edu_quality.public.py.utils import get_div_students as get_div_stud


@frappe.whitelist()
def get_columns(assessment_group, filters):
    if not assessment_group:
        return []
    assess_group = frappe.get_doc("Assessment Group", assessment_group)
    if assess_group.is_group or assess_group.custom_is_composite:
        frappe.throw(
            "Can't enter marks of a assessment group of group type or composite type"
        )

    if assess_group.custom_is_composite:
        return get_composite_exam_columns(assess_group, filters)
    else:
        return get_subject_criteria_columns(assess_group, filters)


def get_subject_criteria_columns(assess_group, filters):
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")
    assess_plan_cr_qb = frappe.qb.DocType("Assessment Plan Criteria")
    division = filters.get("division")

    query = (
        frappe.qb.from_(assess_plan_qb)
        .inner_join(assess_plan_cr_qb)
        .on(assess_plan_qb.name == assess_plan_cr_qb.parent)
        .where(
            (assess_plan_qb.assessment_group == assess_group.get("name"))
            & (assess_plan_qb.student_group == division)
            & (assess_plan_qb.docstatus == 1)
        )
    ).select(
        assess_plan_qb.star,
        assess_plan_cr_qb.assessment_criteria,
        assess_plan_cr_qb.maximum_score,
        assess_plan_cr_qb.custom_exam_type,
        assess_plan_cr_qb.custom_scale,
        assess_plan_cr_qb.custom_allow_revaluation,
        assess_plan_cr_qb.name.as_("assess_criteria_row_name"),
        assess_plan_qb.custom_scoring_type,
        assess_plan_qb.grading_scale,
    )

    data = query.run(as_dict=True) or []
    # for plan in data:
    #     if plan.get("docstatus") in [0, 2]:
    #         frappe.throw(
    #             "One or more assessment plan in the group is non submitted, submit all the plans in the group to score"
    #         )
    #         return []
    return [generate_column_dict(assess_plan) for assess_plan in data]


def get_composite_exam_columns(assess_group, filters):
    """Renders columns without union as they are required to be available in marks entry"""
    columns = []
    for atom_assess_group in assess_group.get("custom_composite_exams"):
        columns = [
            *columns,
            *get_subject_criteria_columns(
                {"name": atom_assess_group.assesment_group}, filters
            ),
        ]
    return columns


def generate_column_dict(assess_plan):
    scoring_type = assess_plan.get("custom_scoring_type")
    grading_scale = assess_plan.get("grading_scale")
    type_string = ""

    if scoring_type == "Marks":
        type_string = f"({assess_plan.get('maximum_score')} marks)"
    elif scoring_type == "Grades":
        type_string = f"(Grades - {grading_scale})"
        
    return {
        "fieldname": gen_field_name(assess_plan),
        "label": f"{gen_label(assess_plan)}<br/> {type_string}",
        "maximum_score": assess_plan.get("maximum_score"),
        "assessment_plan": assess_plan.get("name"),
        "assessment_criteria_row_name": assess_plan.get("assess_criteria_row_name"),
        "subject": assess_plan.get("subject"),
        "assessment_criteria": assess_plan.get("assessment_criteria"),
        "is_criteria": 1,
        "scoring_type": assess_plan.get("custom_scoring_type"),
        "custom_scale": assess_plan.get("custom_scale"),
    }


def gen_label(assess_plan):
    return f"{assess_plan.get('course')} {assess_plan.get('assessment_criteria')}"


def gen_field_name(assess_plan):
    return f"{to_snake_case(assess_plan.get('name'))} - ({assess_plan.get('course')}-{assess_plan.get('assessment_criteria')})"


def get_div_students(division):
    data = get_div_stud(division)
    return [
        {"ref_no": student.get("student"), "student_name": student.get("student_name")}
        for student in data
    ]


def get_data(filters, criterias):
    division = filters.get("division")
    students = get_div_students(division)
    get_earlier_marks(filters, students, criterias)
    return students


def get_earlier_marks(filters, students, criterias):
    cr_hash = gen_hash(criterias)
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assessment_det_qb = frappe.qb.DocType("Assessment Result Detail")
    students_list = [student.get("ref_no") for student in students]
    plan_list = [criteria.get("assessment_plan") for criteria in criterias]

    query = (
        frappe.qb.from_(assess_res_qb)
        .left_join(assessment_det_qb)
        .on((assessment_det_qb.parent == assess_res_qb.name))
        .where(
            (assess_res_qb.assessment_plan.isin(plan_list or [None]))
            & (assess_res_qb.student.isin(students_list or [None]))
            & (assess_res_qb.docstatus.isin([0, 1]))
        )
        .select(
            assess_res_qb.star,
            assessment_det_qb.assessment_criteria,
            assessment_det_qb.score,
            assessment_det_qb.custom_is_absent,
            assessment_det_qb.grade,
            assess_res_qb.custom_scoring_type,
        )
    )

    data = query.run(as_dict=True)

    students_res = {}
    for assess_res in data:
        student = assess_res.get("student")
        if assess_res.student in students_res:
            students_res[student].append(assess_res)
        else:
            students_res[student] = [assess_res]

    for student in students:
        curr_ref = student.get("ref_no")
        if curr_ref not in students_res:
            continue
        for assess_res in students_res[curr_ref]:
            scoring_type = assess_res.get("custom_scoring_type")
            is_absent = assess_res.get("custom_is_absent")
            score = assess_res.get("score")
            grade = assess_res.get("grade")
            assess_plan = {
                "name": assess_res.get("assessment_plan"),
                "course": assess_res.get("course"),
                "assessment_criteria": assess_res.get("assessment_criteria"),
            }
            if is_absent:
                student[gen_field_name(assess_plan)] = is_absent
            elif scoring_type == "Marks":
                student[gen_field_name(assess_plan)] = score
            elif scoring_type == "Grades":
                student[gen_field_name(assess_plan)] = grade
            else:
                student[gen_field_name(assess_plan)] = 0
    return students


def execute(filters=None):
    assessment_group = filters.get("assessment_group")
    criterias = get_columns(assessment_group, filters)
    columns = [
        {"fieldname": "ref_no", "label": "Ref No"},
        {"fieldname": "student_name", "label": "Name"},
        *criterias,
    ]
    data = get_data(filters, criterias)
    if not criterias:
        return [], []
    return columns, data


# edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.get_divisions_class_type
@frappe.whitelist()
def get_divisions_class_type(txt, filters):
    filters = json.loads(filters) if isinstance(filters, str) else filters
    class_type = filters.get("class")
    school = filters.get("school")
    academic_year = filters.get("academic_year")
    all_programs = frappe.db.get_all(
        "Program", filters={"school": school, "program_name": class_type}
    )
    program_list = [program.get("name") for program in all_programs] or []
    all_divs = (
        frappe.db.get_all(
            "Student Group",
            filters=[
                ["name", "like", f"%{txt}%"],
                ["program", "in", program_list],
                ["academic_year", "=", academic_year],
            ],
        )
        or []
    )
    return [{"value": div.get("name"), "description": ""} for div in all_divs]


# edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.do_mark_entry
@frappe.whitelist()
def do_mark_entry(data, filters):
    data = json.loads(data) if isinstance(data, str) else data
    filters = json.loads(filters) if isinstance(filters, str) else filters

    columns = get_columns(filters.get("assessment_group"), filters)
    hashed_columns = gen_hash(columns)

    for row in data:
        assessment_details = []
        ref_no = row.get("ref_no")
        for column in hashed_columns:
            column_data = hashed_columns[column]
            assessment_plan = column_data.get("assessment_plan")
            fieldname = column_data.get("fieldname")
            assessment_criteria = column_data.get("assessment_criteria")
            if fieldname in row:
                assessment_details.append(
                    {
                        "assessment_criteria": {
                            "name": assessment_criteria,
                            "value": row[fieldname],
                            "scoring_type": column_data.get("scoring_type"),
                            "custom_scale": column_data.get("custom_scale"),
                        },
                        "assessment_plan": assessment_plan,
                    }
                )
        enter_marks(ref_no, assessment_details)


def enter_marks(ref_no, criterias):
    plan_hash = {}
    for criteria in criterias:
        assessment_plan = criteria.get("assessment_plan")
        if assessment_plan not in plan_hash:
            plan_hash[assessment_plan] = [criteria]
        else:
            plan_hash[assessment_plan].append(criteria)
    for plan in plan_hash:
        enter_individual_marks(ref_no, plan_hash[plan], plan)


def enter_individual_marks(
    ref_no,
    criterias,
    assessment_plan,
):
    assessment_details = []
    is_absent = 0
    for criteria in criterias:
        assessment_criteria = criteria.get("assessment_criteria")
        name = assessment_criteria.get("name")
        score = assessment_criteria.get("value")
        scale = assessment_criteria.get("custom_scale")
        scoring_type = assessment_criteria.get("scoring_type")

        if str(score).lower() == "ab":
            score = 0
            is_absent = 1

        if scoring_type == "Marks":
            assessment_details.append(
                {
                    "assessment_criteria": name,
                    "score": flt(score) or 0,
                    "custom_scale": scale,
                    "custom_is_absent": is_absent,
                }
            )
        elif scoring_type == "Grades":

            assessment_details.append(
                {
                    "assessment_criteria": name,
                    "score": 0,
                    "custom_is_absent": is_absent,
                    "custom_scale": scale,
                    "grade": str(score).upper(),
                }
            )

    assessment_result = get_assessment_result_doc(ref_no, assessment_plan)
    assessment_result.update(
        {
            "student": ref_no,
            "assessment_plan": assessment_plan,
            "details": assessment_details,
        }
    )
    assessment_result.save()


def get_assessment_result_doc(ref_no, assessment_plan):
    assessment_result = frappe.get_all(
        "Assessment Result",
        filters={
            "student": ref_no,
            "assessment_plan": assessment_plan,
            "docstatus": ["not in", [1, 2]],
        },
    )

    if assessment_result:
        doc = frappe.get_doc("Assessment Result", assessment_result[0])
        if doc.docstatus == 0:
            return doc
        elif doc.docstatus == 1:
            frappe.msgprint(_("Result already Submitted"))
            return None
    else:
        return frappe.new_doc("Assessment Result")


def gen_hash(columns):
    hashmap = {}
    for column in columns:
        field_name = column.get("fieldname")
        if field_name not in hashmap:
            hashmap[field_name] = column

    return hashmap
