# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt


import frappe
from edu_quality.public.py.utils import to_snake_case


@frappe.whitelist()
def get_columns(assessment_group):
    assess_group = frappe.get_doc("Assessment Group", assessment_group)
    if assess_group.is_group:
        frappe.throw("Can't calculate result of a assessment group of group type")

    if assess_group.custom_is_composite:
        return get_composite_exam_columns(assess_group)
    else:
        return get_subject_criteria_columns(assess_group)


def get_subject_criteria_columns(assess_group):
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")
    assess_plan_cr_qb = frappe.qb.DocType("Assessment Plan Criteria")

    query = (
        frappe.qb.from_(assess_plan_qb)
        .inner_join(assess_plan_cr_qb)
        .on(assess_plan_qb.name == assess_plan_cr_qb.parent)
        .where((assess_plan_qb.assessment_group == assess_group.get("name")))
    ).select(
        assess_plan_qb.star,
        assess_plan_cr_qb.assessment_criteria,
        assess_plan_cr_qb.maximum_score,
        assess_plan_cr_qb.custom_exam_type,
        assess_plan_cr_qb.custom_scale,
        assess_plan_cr_qb.custom_allow_revaluation,
        assess_plan_cr_qb.custom_textbook,
        assess_plan_cr_qb.name.as_("assess_criteria_row_name"),
    )
    data = query.run(as_dict=True) or []
    return [generate_column_dict(assess_plan) for assess_plan in data]


def get_composite_exam_columns(assess_group):
    """Renders columns without union as they are required to be available in marks entry"""
    columns = []
    for atom_assess_group in assess_group.get("custom_composite_exams"):
        columns = [
            *columns,
            *get_subject_criteria_columns({"name": atom_assess_group.assesment_group}),
        ]
    return columns


def generate_column_dict(assess_plan):
    return {
        "fieldname": gen_field_name(assess_plan),
        "label": gen_field_name(assess_plan),
        "assessment_plan": assess_plan.get("name"),
        "assessment_criteria_row_name": assess_plan.get("assess_criteria_row_name"),
        "subject": assess_plan.get("subject"),
        "is_criteria": 1,
    }


def gen_field_name(assess_plan):
    return f"{to_snake_case(assess_plan.get('name'))} - ({assess_plan.get('course')}-{assess_plan.get('assessment_criteria')})"


def get_div_students(division):
    frappe.errprint(division)
    data = frappe.get_list(
        "Program Enrollment",
        filters={"docstatus": 1, "student_group": ["in", division]},
        fields=["student_name", "name", "student"],
    )
    frappe.errprint(data)
    return [
        {"ref_no": student.get("student"), "student_name": student.get("student_name")}
        for student in data
    ]


def get_data(filters):
    division = filters.get("division")
    return get_div_students(division)


def execute(filters=None):
    assessment_group = filters.get("assessment_group")
    columns, data = [
        {"fieldname": "ref_no", "label": "Ref No"},
        {"fieldname": "student_name", "label": "Name"},
        *get_columns(assessment_group),
    ], get_data(filters)
    return columns, data
