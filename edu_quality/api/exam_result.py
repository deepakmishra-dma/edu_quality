import frappe
from frappe.query_builder import Field


def get_div_students(division):

    data = frappe.db.get_all(
        "Student Group Student",
        filters={"parent": division},
        fields=["student_name", "name", "student"],
    )
    return [student.get("student") for student in data]


def get_all_assessment_plans(assessment_group, program, div):
    assess_group_qb = frappe.qb.DocType("Assessment Group")
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")

    div_query = assess_plan_qb.student_group.isnotnull()
    if div:
        div_query = assess_plan_qb.student_group == div
    query = (
        frappe.qb.from_(assess_group_qb)
        .inner_join(assess_plan_qb)
        .on(assess_group_qb.name == assess_plan_qb.assessment_group)
        .where(
            (assess_group_qb.name == assessment_group)
            & div_query
            & (assess_plan_qb.program == program)
            & (assess_plan_qb.docstatus == 1)
        )
        .select(
            assess_plan_qb.name,
            assess_plan_qb.student_group,
            assess_plan_qb.custom_calculate_ranks,
        )
    )

    data = query.run(as_dict=True)
    return data


def check_assessment_plan_in_group(assessment_plans):
    all_errors = []
    already_submitted = []
    for plan in assessment_plans:
        div = plan.get("student_group")
        plan_name = plan.get("name")
        errors = check_assessment_plan_in_div(plan_name, div)
        all_errors.extend(errors)

    if already_submitted:
        frappe.prompt("There are submitted results already, proceed ?")
    if all_errors:
        frappe.throw("<br/>".join(all_errors))
    return all_errors


def get_assessment_plan_in_div(assessment_plan, division, students):
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")

    query = (
        frappe.qb.from_(assess_res_qb)
        .inner_join(assess_res_de_qb)
        .on(assess_res_de_qb.parent == assess_res_qb.name)
        .where(
            (
                assess_res_qb.student.isin(students or [None])
                & (assess_res_qb.assessment_plan == assessment_plan)
                & (assess_res_de_qb.score.isnotnull())
                & (assess_res_qb.docstatus.isin([1, 0]))
            )
        )
        .select(
            assess_res_qb.student,
            assess_res_qb.assessment_plan,
            assess_res_de_qb.assessment_criteria,
            assess_res_de_qb.score,
            assess_res_qb.name,
            assess_res_qb.docstatus,
            assess_res_qb.custom_is_absent,
        )
    )
    return query.run(as_dict=True)


def check_assessment_plan_in_div(assessment_plan, division):
    students = get_div_students(division)
    data = get_assessment_plan_in_div(assessment_plan, division, students)

    return diff_students_and_results(students, data, assessment_plan)


def diff_students_and_results(students, results, assessment_plan):
    no_data_students = {}
    result_hash = {}
    already_submitted = []
    errors = []

    for result in results:
        student = result.get("student")

        if result.get("score") == None:
            if no_data_students.get(student):
                no_data_students[student].append(result)
            else:
                no_data_students[student] = [result]

        elif result_hash.get(student):
            result_hash[student].append(result)
        else:
            result_hash[student] = [result]
        if result.get("docstatus") == 1:
            already_submitted.append({student: "student", "result": result.get("name")})

    for student in students:
        if student not in result_hash and student not in no_data_students:
            errors.append(
                f"No Result Created for student {student} for assessment_plan {assessment_plan}"
            )
        elif student not in result_hash and student in no_data_students:
            errors.append(f"Data is missing for {student} in {assessment_plan}")

    return errors


@frappe.whitelist()
def process_result(assessment_group, academic_year, program, div=None):
    assessment_plans = get_all_assessment_plans(assessment_group, program, div)
    errors = check_assessment_plan_in_group(assessment_plans)
    if errors:
        return errors

    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")

    plans = [plan.get("name") for plan in assessment_plans]

    query = (
        frappe.qb.from_(assess_res_qb)
        .inner_join(assess_res_de_qb)
        .on(assess_res_de_qb.parent == assess_res_qb.name)
        .where(
            (
                (assess_res_qb.docstatus.isin([0, 1]))
                & assess_res_qb.assessment_plan.isin(plans or [None])
                & (assess_res_de_qb.score.isnotnull())
            )
        )
        .select(
            assess_res_qb.student,
            assess_res_qb.docstatus,
            assess_res_qb.assessment_plan,
            assess_res_de_qb.assessment_criteria,
            assess_res_de_qb.score,
            assess_res_de_qb.name,
            assess_res_de_qb.custom_scale,
            assess_res_de_qb.parent,
            assess_res_qb.custom_is_absent,
        )
    )

    result_data = query.run(as_dict=True)
    modified_result = {}

    for result in result_data:
        score = result.get("score")
        scale = result.get("custom_scale")
        parent = result.get("parent")
        docstatus = result.get("docstatus")
        if result.get("custom_is_absent") == 0:
            frappe.db.set_value(
                "Assessment Result Detail",
                result.get("name"),
                "custom_processed_result",
                score * (scale),
            )
            modified_result[parent] = docstatus

    for parent in modified_result:

        if modified_result[parent] == 1:
            assess_result = frappe.get_doc("Assessment Result", parent)
            assess_result.cancel()
            amended_doc = frappe.copy_doc(assess_result)
            amended_doc.amended_from = assess_result.name
            amended_doc.submit()
            continue
        frappe.db.set_value("Assessment Result", parent, "docstatus", 1)

    for assess_plan in assessment_plans:
        plan = assess_plan.get("name")
        calculate_ranking = assess_plan.get("custom_calculate_ranks")
        if calculate_ranking:
            calculate_ordering(plan)
    frappe.msgprint(
        "Successfully Processed all the results matching the criteria provided"
    )


def calculate_ordering(assessment_plan):
    data = frappe.db.sql(
        """
        Update `tabAssessment Result` 
    INNER JOIN (SELECT 
        RANK() OVER (ORDER BY custom_total_processed_score DESC) AS ranking,
        name
    FROM 
        `tabAssessment Result`
    WHERE 
        assessment_plan = %(id)s
        AND docstatus = 1) AS ranked_table ON  `tabAssessment Result`.name = ranked_table.name
SET  `tabAssessment Result`.custom_rank = ranked_table.ranking;
""",
        values={"id": assessment_plan},
        as_dict=True,
    )
