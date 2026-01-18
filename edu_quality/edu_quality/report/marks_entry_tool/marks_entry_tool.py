# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt


import frappe
from edu_quality.public.py.utils import to_snake_case
import json
from frappe.utils import flt
from edu_quality.public.py.utils import get_div_students as get_div_stud
from frappe.model.mapper import get_mapped_doc


def get_default_columns(assessment_group, filters):
    """Get default Columns which are to be shown and not computed like ref no, question etc."""

    if not assessment_group:
        return []

    assess_group = frappe.get_cached_doc("Assessment Group", assessment_group)

    if not assess_group.custom_is_kg_exam:
        default_columns = [
            {"fieldname": "ref_no", "label": "Ref No"},
            {"fieldname": "student_name", "label": "Name"},
        ]

    if filters.get("remarks", None):
        default_columns = [
            {"fieldname": "feature", "label": "Feature"},
        ]

    if assess_group.custom_is_kg_exam or filters.get("remarks", None):
        default_columns = [
            {"fieldname": "question", "label": "Question"},
        ]
    return default_columns


@frappe.whitelist()
def get_columns(assessment_group, filters):
    """Get  Columns which are computed like Student ref no in descriptive or criteria in normal"""
    if not assessment_group:
        return []

    assess_group = frappe.get_cached_doc("Assessment Group", assessment_group)

    if assess_group.is_group or assess_group.custom_is_composite:
        frappe.throw(
            "Can't enter marks of a assessment group of group type or composite type"
        )

    if assess_group.custom_is_composite:
        columns = get_composite_exam_columns(assess_group, filters)
    elif assess_group.custom_is_kg_exam or filters.get("remarks", None):
        columns = get_stud_wise_columns(assess_group, filters)
    else:
        columns = get_subject_criteria_columns(assess_group, filters)

    return columns or []


def get_subject_criteria_columns(assess_group, filters):
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")
    assess_plan_cr_qb = frappe.qb.DocType("Assessment Plan Criteria")
    subject_qb = frappe.qb.DocType("Course")
    division = filters.get("division")

    query = (
        (
            frappe.qb.from_(assess_plan_qb)
            .inner_join(assess_plan_cr_qb)
            .on(assess_plan_qb.name == assess_plan_cr_qb.parent)
            .inner_join(subject_qb)
            .on(assess_plan_qb.course == subject_qb.name)
            .where(
                (assess_plan_qb.assessment_group == assess_group.get("name"))
                & (assess_plan_qb.student_group == division)
                & (assess_plan_qb.docstatus == 1)
            )
        )
        .orderby(
            assess_plan_qb.course,
            assess_plan_qb.custom_type,
            assess_plan_cr_qb.assessment_criteria,
        )
        .select(
            assess_plan_qb.star,
            assess_plan_cr_qb.assessment_criteria,
            assess_plan_cr_qb.maximum_score,
            assess_plan_cr_qb.custom_exam_type,
            assess_plan_cr_qb.custom_scale,
            assess_plan_cr_qb.custom_allow_revaluation,
            subject_qb.custom_short_code,
            assess_plan_cr_qb.name.as_("assess_criteria_row_name"),
            assess_plan_qb.custom_scoring_type,
            assess_plan_qb.grading_scale,
        )
    )

    data = query.run(as_dict=True) or []
    # for plan in data:
    #     if plan.get("docstatus") in [0, 2]:
    #         frappe.throw(
    #             "One or more assessment plan in the group is non submitted, submit all the plans in the group to score"
    #         )
    #         return []
    return [generate_column_dict(assess_plan) for assess_plan in data]


def get_stud_wise_columns(assessment_group, filters):
    division = filters.get("division")
    mode = filters.get("mode")
    ref_no = filters.get("ref_no")

    if not mode:
        students = get_div_students(division)
    else:
        students = get_div_students(division, ref_no)

    return [generate_desc_column_dict(student) for student in students]


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


def generate_desc_column_dict(student):
    return {
        "fieldname": gen_desc_field_name(student),
        "label": f"{gen_desc_label(student)}<br/>",
        "maximum_score": student.get("maximum_score"),
        # "assessment_plan": desc_exam.get("name"),
        # "assessment_criteria_row_name": desc_exam.get("desc_name_row_name"),
        # "subject": desc_exam.get("subject"),
        # "assessment_criteria": desc_exam.get("question"),
        "is_criteria": 1,
        # "scoring_type": "Grades",
    }


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
        "label": f"{gen_label(assess_plan,assess_plan.get('custom_short_code'))}<br/> {type_string}",
        "maximum_score": assess_plan.get("maximum_score"),
        "assessment_plan": assess_plan.get("name"),
        "assessment_criteria_row_name": assess_plan.get("assess_criteria_row_name"),
        "subject": assess_plan.get("subject"),
        "assessment_criteria": assess_plan.get("assessment_criteria"),
        "is_criteria": 1,
        "scoring_type": assess_plan.get("custom_scoring_type"),
        "custom_scale": assess_plan.get("custom_scale"),
    }


def gen_desc_label(student):
    return f"{student.get('roll_no')}<br/>({student.get('ref_no')})"


def gen_label(assess_plan, short_code):
    return f"{short_code or assess_plan.get('course') or assess_plan.get('subject')} {assess_plan.get('assessment_criteria')}"


def gen_desc_field_name(student):
    return student.get("ref_no")


def gen_desc_ques_field(data):
    return f"{data.get('assessment-plan')} {data.get('question')} {data.get('assessment_criteria')}"


def gen_field_name(assess_plan, is_extra=False):
    if is_extra:
        return f"{to_snake_case(assess_plan.get('name'))} - ({assess_plan.get('course')}-{assess_plan.get('assessment_criteria')})_is_extra"

    return f"{to_snake_case(assess_plan.get('name'))} - ({assess_plan.get('course')}-{assess_plan.get('assessment_criteria')})"


def get_div_students(division, mode=None, ref_no=None):
    """Get Students inside a div using program enrollment that are submitted, if mode is true, fetches the student that passed the ref no"""
    if not mode:
        data = get_div_stud(division)
    else:
        data = get_div_stud(division, ref_no)

    return [
        {
            "ref_no": student.get("student"),
            "student_name": student.get("student_name"),
            "roll_no": student.get("roll_no"),
        }
        for student in data
    ]


def get_data(filters, criterias, assessment_group_doc):
    mode = filters.get("mode")
    ref_no = filters.get("ref_no")
    division = filters.get("division")
    students = get_div_students(division, mode, ref_no)

    if not assessment_group_doc.custom_is_kg_exam and not filters.get("remarks"):
        get_earlier_marks(filters, students, criterias)
    elif filters.get("remarks"):
        return get_remarks_earlier_marks(filters, students)
    else:
        return get_desc_earlier_marks(filters, students)

    return students


def get_desc_questions(asess_plans_query):
    assess_plan_cr_qb = frappe.qb.DocType("Assessment Plan Criteria")
    desc_exam_ques_qb = frappe.qb.DocType("Descriptive Question")

    paper_query = (
        frappe.qb.from_(asess_plans_query)
        .inner_join(assess_plan_cr_qb)
        .on(asess_plans_query.name == assess_plan_cr_qb.parent)
        .inner_join(desc_exam_ques_qb)
        .on(desc_exam_ques_qb.name == assess_plan_cr_qb.custom_question)
        .select(
            asess_plans_query.name.as_("assessment_plan"),
            desc_exam_ques_qb.name.as_("question"),
            desc_exam_ques_qb.max_marks,
            desc_exam_ques_qb.min_marks,
            assess_plan_cr_qb.assessment_criteria,
            desc_exam_ques_qb.parent_descriptive_question,
        )
    )
    return paper_query.run(as_dict=True)


def get_remark_questions(assess_group):
    assess_group = frappe.get_doc("Assessment Group", assess_group)
    remark_template = assess_group.custom_remarks_template_id
    template_qb = frappe.qb.DocType("Assessment Remarks Template")
    scoring_qb = frappe.qb.DocType("Assessment Remarks Scoring")

    query = (
        frappe.qb.from_(template_qb)
        .inner_join(scoring_qb)
        .on(template_qb.name == scoring_qb.parent)
        .where(template_qb.name == remark_template)
        .groupby(scoring_qb.feature)
        .select(scoring_qb.feature)
    )

    data = query.run(as_dict=True)
    return data


def get_remarks_earlier_marks(filters, students):
    assessment_group = filters.get("assessment_group")
    students_list = [student.get("ref_no") for student in students]
    assess_res_qb = frappe.qb.DocType("Remark Result")

    assess_res_de_qb = frappe.qb.DocType("Assessment Result Remark")
    remark_questions = get_remark_questions(assessment_group)

    query = (
        frappe.qb.from_(assess_res_qb)
        .inner_join(assess_res_de_qb)
        .on(assess_res_qb.name == assess_res_de_qb.parent)
        .where(
            (assess_res_qb.student.isin(students_list or [None]))
            & (assess_res_qb.assessment_group == assessment_group)
            & (assess_res_qb.docstatus.isin([0, 1]))
        )
        .select(
            assess_res_qb.assessment_group,
            assess_res_qb.student,
            assess_res_de_qb.score,
            assess_res_de_qb.remark.as_("feature"),
        )
    )

    questions_hash = {}
    data = query.run(as_dict=True)

    for remark in remark_questions:
        remark_name = remark.get("feature")
        if remark_name not in questions_hash:
            questions_hash[remark_name] = {
                "feature": remark_name,
            }

    for remark in data:
        remark_name = remark.get("feature")

        student = remark.get("student")
        score = remark.get("score")
        is_absent = remark.get("custom_is_absent")
        grade = None

        if remark_name in questions_hash:
            questions_hash[remark_name] = {
                **questions_hash[remark_name],
                "feature": remark_name,
                student: parse_score(is_absent, "Marks", score, grade),
            }
    return [question for question in questions_hash.values()]


def get_desc_earlier_marks(filters, students):
    assessment_group = filters.get("assessment_group")

    assess_plan_qb = frappe.qb.DocType("Assessment Plan")
    assess_plan_cr_qb = frappe.qb.DocType("Assessment Plan Criteria")

    desc_exam_ques_qb = frappe.qb.DocType("Descriptive Question")
    assess_res_qb = frappe.qb.DocType("Assessment Result")

    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")
    students_list = [student.get("ref_no") for student in students]

    asess_plans_query = (
        frappe.qb.from_(assess_plan_qb)
        .where(
            (assess_plan_qb.assessment_group == assessment_group)
            & (assess_plan_qb.docstatus == 1)
            & (assess_plan_qb.custom_is_descriptive)
        )
        .select(assess_plan_qb.star)
    )

    questions_data = get_desc_questions(asess_plans_query)
    all_plans = [plan.get("assessment_plan") for plan in questions_data]
    query = (
        frappe.qb.from_(assess_res_qb)
        .inner_join(assess_res_de_qb)
        .on(assess_res_qb.name == assess_res_de_qb.parent)
        .where(
            (assess_res_qb.student.isin(students_list or [None]))
            & (assess_res_qb.assessment_plan.isin(all_plans or [None]))
            & (assess_res_qb.docstatus.isin([0, 1]))
        )
        .select(
            assess_res_qb.assessment_plan,
            assess_res_qb.student,
            assess_res_qb.custom_scoring_type,
            assess_res_de_qb.score,
            assess_res_de_qb.custom_question.as_("question"),
            assess_res_de_qb.assessment_criteria,
            assess_res_de_qb.custom_is_absent,
            assess_res_de_qb.grade,
        )
    )

    questions_hash = {}
    data = query.run(as_dict=True)

    for question in questions_data:
        question_name = question.get("question")
        criteria = question.get("assessment_criteria")
        assess_plan = question.get("assessment_plan")

        if gen_desc_ques_field(question) not in questions_hash:
            questions_hash[gen_desc_ques_field(question)] = {
                "question": question_name,
                "assessment_plan": assess_plan,
                "assessment_criteria": criteria,
            }

    for question in data:
        question_name = question.get("question")
        criteria = question.get("assessment_criteria")
        assess_plan = question.get("assessment_plan")
        student = question.get("student")
        score = question.get("score")
        is_absent = question.get("custom_is_absent")
        scoring_type = question.get("custom_scoring_type")
        grade = question.get("grade")

        if gen_desc_ques_field(question) in questions_hash:
            questions_hash[gen_desc_ques_field(question)] = {
                **questions_hash[gen_desc_ques_field(question)],
                "question": question_name,
                "assessment_plan": assess_plan,
                "assessment_criteria": criteria,
                student: parse_score(is_absent, scoring_type, score, grade),
            }

    return [question for question in questions_hash.values()]


def get_earlier_marks(filters, students, criterias):
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
            assessment_det_qb.custom_online_assessment,
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
            docstatus = assess_res.get("docstatus")
            online_assess = assess_res.get("custom_online_assessment")
            assessment_plan = assess_res.get("assessment_plan")
            course = assess_res.get("course")
            criteria = assess_res.get("assessment_criteria")

            assess_plan = {
                "name": assessment_plan,
                "course": course,
                "assessment_criteria": criteria,
            }
            student[gen_field_name(assess_plan)] = parse_score(
                is_absent, scoring_type, score, grade
            )

            student[gen_field_name(assess_plan, True)] = {
                "docstatus": docstatus,
                "online_assess": online_assess,
            }

    return students


def parse_score(is_absent, scoring_type, score, grade):
    if is_absent:
        return "-"
    elif scoring_type == "Marks":
        return score
    elif scoring_type == "Grades":
        return grade
    else:
        return 0


def execute(filters=None):
    assessment_group = filters.get("assessment_group")
    assess_group_doc = frappe.get_doc("Assessment Group", assessment_group)
    default_columns = get_default_columns(assessment_group, filters)
    columns = get_columns(assessment_group, filters)
    data = get_data(filters, columns, assess_group_doc)
    all_columns = [*default_columns, *columns]

    if not columns:
        return [], []
    return all_columns, data


def assessment_mark_entry(data, hashed_columns, mode):
    for row in data:
        assessment_details = []
        ref_no = row.get("ref_no")

        for column in hashed_columns:
            column_data = hashed_columns[column]
            assessment_plan, fieldname, assessment_criteria = (
                column_data.get("assessment_plan"),
                column_data.get("fieldname"),
                column_data.get("assessment_criteria"),
            )

            if fieldname in row:
                assessment_details.append(
                    {
                        "assessment_criteria": {
                            "name": assessment_criteria,
                            "value": get_field_value(row, fieldname),
                            "scoring_type": column_data.get("scoring_type"),
                            "custom_scale": column_data.get("custom_scale"),
                            "custom_online_assessment": mode or 0,
                        },
                        "assessment_plan": assessment_plan,
                    }
                )
        enter_marks(ref_no, assessment_details)


def enter_remark(data, hashed_columns, filters):
    student_data = {}
    assessment_group = filters.get("assessment_group")
    for datum in data:
        feature = datum.get("feature")

    for student in hashed_columns:
        if student in datum:
            payload = {
                "assessment_criteria": {
                    "name": "Remark",
                    "value": get_field_value(datum, student),
                    "feature": feature,
                },
                "assessment_group": assessment_group,
            }
            if student not in student_data:
                student_data[student] = {}
                student_data[student] = [payload]
            else:
                student_data[student].append(payload)

    for student in student_data:
        enter_remark_mark(student, assessment_group, student_data[student])


def enter_remark_mark(ref_no, assessment_group, remark_data):
    assessment_details = []
    remark_result = get_remark_result_doc(ref_no, assessment_group)

    if not remark_result:
        return

    assessment_details = [i for i in remark_result.remarks]

    for remark in remark_data:
        add_assessment_criteria(assessment_details, remark, None, True)

    remark_result.update(
        {
            "student": ref_no,
            "assessment_group": assessment_group,
            "remarks": assessment_details,
        }
    )
    remark_result.save()


def enter_column_wise_mark(data, hashed_columns):
    student_data = {}

    for datum in data:
        assessment_plan = datum.get("assessment_plan")
        question = datum.get("question")
        parent_question = datum.get("descriptive_parent_question")
        for student in hashed_columns:
            if student in datum:
                criteria = {
                    "assessment_criteria": {
                        "name": "Descriptive Question",
                        "value": get_field_value(datum, student),
                        "custom_question": question,
                        "parent_question": parent_question,
                    },
                    "assessment_plan": assessment_plan,
                }

                if student not in student_data:
                    student_data[student] = {}
                    student_data[student][assessment_plan] = [criteria]
                elif assessment_plan not in student_data[student]:
                    student_data[student][assessment_plan] = [criteria]
                else:
                    student_data[student][assessment_plan].append(criteria)

    for student in student_data:
        for plan in student_data[student]:
            for assessment_plan in student_data[student][plan]:
                enter_criteria_marks(student, student_data[student][plan], plan, True)


# edu_quality.edu_quality.report.marks_entry_tool.marks_entry_tool.do_mark_entry
@frappe.whitelist()
def do_mark_entry(data, filters):
    data = json.loads(data) if isinstance(data, str) else data
    filters = json.loads(filters) if isinstance(filters, str) else filters
    mode = filters.get("mode")
    columns = get_columns(filters.get("assessment_group"), filters)

    # get all the columns which should belong to the report with specified filter
    hashed_columns = gen_hash(columns)

    assessment_group_doc = frappe.get_cached_doc(
        "Assessment Group", filters.get("assessment_group")
    )

    if not assessment_group_doc.custom_is_kg_exam and not filters.get("remarks"):
        assessment_mark_entry(data, hashed_columns, mode)
    elif filters.get("remarks"):
        enter_remark(data, hashed_columns, filters)
    else:
        enter_column_wise_mark(data, hashed_columns)


def enter_marks(ref_no, criterias):
    plan_hash = {}
    for criteria in criterias:
        assessment_plan = criteria.get("assessment_plan")
        if assessment_plan not in plan_hash:
            plan_hash[assessment_plan] = [criteria]
        else:
            plan_hash[assessment_plan].append(criteria)
    for plan in plan_hash:
        enter_criteria_marks(ref_no, plan_hash[plan], plan)


def get_field_value(row, fieldname):
    """Get field value from the marks entered in table cell"""

    if isinstance(row[fieldname], dict):
        return row.get(fieldname, {}).get("content")
    return row[fieldname]


def enter_criteria_marks(
    ref_no,
    criterias,
    assessment_plan,
    is_descriptive=None,
):
    assessment_details = []
    assessment_result = get_assessment_result_doc(ref_no, assessment_plan)

    if not assessment_result:
        return

    assessment_details = [i for i in assessment_result.details]

    for criteria in criterias:
        add_assessment_criteria(assessment_details, criteria, is_descriptive)

    assessment_result.update(
        {
            "student": ref_no,
            "assessment_plan": assessment_plan,
            "details": assessment_details,
        }
    )
    assessment_result.save()


def get_assessment_result_doc(ref_no, assessment_plan):
    """Gets existing Result doc if doesnt exist create new, if subitted returns None"""

    assessment_result = frappe.get_all(
        "Assessment Result",
        filters={
            "student": ref_no,
            "assessment_plan": assessment_plan,
            "docstatus": ["not in", [2]],
        },
    )

    if assessment_result:
        doc = frappe.get_doc("Assessment Result", assessment_result[0])
        if doc.docstatus == 0:
            return doc
        elif doc.docstatus == 1:
            return None
    else:
        return frappe.new_doc("Assessment Result")


def get_remark_result_doc(ref_no, assessment_group):
    """Gets existing Remark Result doc if doesnt exist create new, if subitted returns None"""

    remark_result = frappe.get_all(
        "Remark Result",
        filters={
            "student": ref_no,
            "assessment_group": assessment_group,
            "docstatus": ["not in", [2]],
        },
    )

    if remark_result:
        doc = frappe.get_doc("Remark Result", remark_result[0])
        if doc.docstatus == 0:
            return doc
        elif doc.docstatus == 1:
            return None
    else:
        return frappe.new_doc("Remark Result")


def add_assessment_criteria(
    assessment_details, criteria, is_descriptive, is_remarks=None
):
    """Adds a criteria in the criteria list in a assessment result"""

    is_absent = 0
    assessment_criteria = criteria.get("assessment_criteria")
    name = assessment_criteria.get("name")
    remark = assessment_criteria.get("feature")
    score = assessment_criteria.get("value")
    scale = assessment_criteria.get("custom_scale")
    scoring_type = assessment_criteria.get("scoring_type")
    online_assessment = assessment_criteria.get("custom_online_assessment")
    question = assessment_criteria.get("custom_question")
    parent_question = assessment_criteria.get("custom_parent_question")

    if str(score).lower() == "-" or score == None:
        score = 0
        is_absent = 1

    if is_remarks:
        append_assessment_criteria(
            assessment_details,
            {
                "remark": remark,
                "score": flt(score) or 0,
            },
            False,
            is_remarks,
        )
    elif is_descriptive:
        append_assessment_criteria(
            assessment_details,
            {
                "assessment_criteria": name,
                "score": flt(score) or 0,
                "custom_question": question,
                "custom_parent_question": parent_question,
                "custom_is_absent": is_absent,
            },
            is_descriptive,
        )

    elif scoring_type == "Marks":
        append_assessment_criteria(
            assessment_details,
            {
                "assessment_criteria": name,
                "score": flt(score) or 0,
                "custom_scale": scale,
                "custom_is_absent": is_absent,
                "custom_online_assessment": online_assessment,
            },
        )

    elif scoring_type == "Grades":
        append_assessment_criteria(
            assessment_details,
            {
                "assessment_criteria": name,
                "score": 0,
                "custom_is_absent": is_absent,
                "custom_scale": scale,
                "grade": str(score).upper(),
                "custom_processed_grade": str(score).upper(),
                "custom_online_assessment": online_assessment,
            },
        )


def gen_desc_assessment_key(criteria, is_descriptive=None, is_remarks=None):
    if is_remarks:
        return criteria.get("remark")
    if not is_descriptive:
        return criteria.get("assessment_criteria")

    return f"{criteria.get('assessment_criteria')}{criteria.get('custom_question')}"


def append_assessment_criteria(
    assessment_details, criteria, is_descriptive=None, is_remarks=None
):
    """Dedupes similar assessment criteria and modifies instead of adding if it already exists"""

    all_criterias = [
        gen_desc_assessment_key(i, is_descriptive, is_remarks)
        for i in assessment_details
    ]

    if gen_desc_assessment_key(criteria, is_descriptive) in all_criterias:
        index = all_criterias.index(
            gen_desc_assessment_key(criteria, is_descriptive, is_remarks)
        )
        assessment_details[index] = criteria
    else:
        assessment_details.append(criteria)


def gen_hash(columns):
    """Generate a dictionary with fieldname specified in get_columns as key"""
    hashmap = {}
    for column in columns:
        field_name = column.get("fieldname")
        if field_name not in hashmap:
            hashmap[field_name] = column

    return hashmap


def cancel_result(assess_plan, ref_no, filters):
    """Cancel an existing result document and amend and create new one and put in draft state"""

    program = filters.get("program")
    academic_year = filters.get("academic_year")
    if frappe.db.exists(
        "Assessment Result",
        {
            "docstatus": 1,
            "student": ref_no,
            "academic_year": academic_year,
            "program": program,
            "assessment_plan": assess_plan,
        },
    ):
        res_doc = frappe.get_doc(
            "Assessment Result",
            {
                "docstatus": 1,
                "student": ref_no,
                "academic_year": academic_year,
                "program": program,
                "assessment_plan": assess_plan,
            },
        )
        res_doc.cancel()

        amended_doc = frappe.copy_doc(res_doc)
        amended_doc.amended_from = res_doc.name
        amended_doc.save()


@frappe.whitelist()
def cancel_result_rows(ref_nos, filters):
    ref_nos = json.loads(ref_nos) if isinstance(ref_nos, str) else ref_nos
    filters = json.loads(filters) if isinstance(filters, str) else filters
    columns = get_columns(filters.get("assessment_group"), filters)

    assess_plans = set([i.get("assessment_plan") for i in columns])

    for ref_no in ref_nos:
        for assess_plan in assess_plans:
            cancel_result(assess_plan, ref_no, filters)


@frappe.whitelist()
def send_marks(**kwargs):
    """
    This function is used to send marks to students for a particular assessment group
    Args:
        assessment_group: str: assessment group name
        division: str: division name optional
    """
    try:
        assessment_group = kwargs.get("assessment_group")
        school = frappe.get_value(
            "Assessment Group", assessment_group, ["custom_school"]
        )
        program = frappe.get_value(
            "Assessment Group", assessment_group, ["custom_program"]
        )
        students = frappe.get_all(
            "Student",
            {"school": school, "program": program, "enabled": 1},
            pluck="name",
        )
        for student in students:
            send_student_marks(student, assessment_group)
        return True
    except:
        frappe.log_error("Failed to send marks to student", frappe.get_traceback())
        return False


def send_student_marks(student, assessment_group):
    """
    This function is used to send marks to students for a particular assessment group
    Args:
        student: str: student name
        assessment_group: str: assessment group name
    """
    student_doc = frappe.get_doc("Student", student)

    current_academic_year = frappe.get_value(
        "Academic Year", {"custom_current_academic_year": 1}, "name"
    )
    student_group = frappe.get_value(
        "Program Enrollment",
        {"student": student_doc.name, "academic_year": current_academic_year},
        "student_group",
    )

    assessment_plan = frappe.get_all(
        "Assessment Plan",
        {
            "student_group": student_group,
            "assessment_group": assessment_group,
            "docstatus": 1,
        },
        pluck="name",
    )
    assessment_result_name = frappe.get_value(
        "Assessment Result",
        {
            "assessment_plan": ["in", assessment_plan],
            "student": student_doc.name,
            "docstatus": 1,
        },
    )

    if assessment_result_name:
        try:
            from nextai.funnel.custom_trigger import trigger_event

            assessment_result = frappe.get_doc(
                "Assessment Result", assessment_result_name, "name"
            )
            trigger_event(doc=assessment_result, event_name="send_processed_result")
        except:
            frappe.log_error("Failed to send marks to student", frappe.get_traceback())
