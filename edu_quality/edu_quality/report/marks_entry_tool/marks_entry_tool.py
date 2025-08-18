# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt


import frappe
from edu_quality.public.py.utils import to_snake_case
import json
from frappe.utils import flt


@frappe.whitelist()
def get_columns(assessment_group, filters):
    assess_group = frappe.get_doc("Assessment Group", assessment_group)
    if assess_group.is_group:
        frappe.throw("Can't calculate result of a assessment group of group type")

    if assess_group.custom_is_composite:
        return get_composite_exam_columns(assess_group, filters)
    else:
        return get_subject_criteria_columns(assess_group, filters)


def get_subject_criteria_columns(assess_group, filters):
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")
    assess_plan_cr_qb = frappe.qb.DocType("Assessment Plan Criteria")
    division = filters.get("division")
    frappe.errprint("haha")
    frappe.errprint(filters)
    query = (
        frappe.qb.from_(assess_plan_qb)
        .inner_join(assess_plan_cr_qb)
        .on(assess_plan_qb.name == assess_plan_cr_qb.parent)
        .where(
            (assess_plan_qb.assessment_group == assess_group.get("name"))
            & (assess_plan_qb.student_group.isin(division or [None]))
        )
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
    return {
        "fieldname": gen_field_name(assess_plan),
        "label": f"{gen_field_name(assess_plan)} Out of marks {assess_plan.get('maximum_score')}",
        "maximum_score": assess_plan.get("maximum_score"),
        "assessment_plan": assess_plan.get("name"),
        "assessment_criteria_row_name": assess_plan.get("assess_criteria_row_name"),
        "subject": assess_plan.get("subject"),
        "assessment_criteria": assess_plan.get("assessment_criteria"),
        "is_criteria": 1,
    }


def gen_field_name(assess_plan):
    return f"{to_snake_case(assess_plan.get('name'))} - ({assess_plan.get('course')}-{assess_plan.get('assessment_criteria')})"


def get_div_students(division):
    data = frappe.get_list(
        "Program Enrollment",
        filters={"docstatus": 1, "student_group": ["in", division or [None]]},
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
        *get_columns(assessment_group, filters),
    ], get_data(filters)
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


def enter_individual_marks(ref_no, criterias, assessment_plan):
    assessment_details = []
    for criteria in criterias:
        assessment_criteria = criteria.get("assessment_criteria")
        name = assessment_criteria.get("name")
        score = assessment_criteria.get("value")
        assessment_details.append(
            {
                "assessment_criteria": name,
                "score": flt(score) or 0,
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
            "docstatus": ("!=", 2),
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
