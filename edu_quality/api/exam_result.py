import frappe
from frappe.query_builder import Field
from frappe.query_builder.functions import Count, GROUP_CONCAT, Sum
from edu_quality.public.py.utils import get_div_students as get_div_stud


def get_div_students(division):
    data = get_div_stud(division)
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
            assess_res_de_qb.custom_is_absent,
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
    if frappe.db.get_value("Assessment Group", assessment_group, "custom_is_composite"):
        process_composite_result(assessment_group, academic_year, program, div=None)
    else:
        process_atomic_exam(assessment_group, academic_year, program, div=None)
    frappe.db.commit()


def process_atomic_exam(assessment_group, academic_year, program, div=None):
    assessment_plans = get_all_assessment_plans(assessment_group, program, div)
    assessment_group_doc = frappe.get_doc("Assessment Group", assessment_group)
    errors = check_assessment_plan_in_group(assessment_plans)
    if errors:
        return errors

    submitted_docs = get_result_from_plans(assessment_plans, False, [1])

    cancel_submitted_atomic_exams(submitted_docs)
    non_submitted_docs = get_result_from_plans(assessment_plans, False, [0])

    modified_result = {}
    total_processed_result = 0
    total_scaled_max_score = 0
    for result in non_submitted_docs:
        (
            score,
            scale,
            parent,
            docstatus,
            is_absent,
            maximum_score,
            custom_scoring_type,
        ) = (
            result.get("score"),
            result.get("custom_scale"),
            result.get("parent"),
            result.get("docstatus"),
            result.get("custom_is_absent"),
            result.get("maximum_score"),
            result.get("custom_scoring_type"),
        )
        if not is_absent and docstatus == 0:
            frappe.db.set_value(
                "Assessment Result Detail",
                result.get("name"),
                "custom_processed_result",
                score * (scale),
            )
            modified_result[parent] = 1
            total_processed_result += score * (scale)
        total_scaled_max_score += maximum_score * scale

    for parent in modified_result:
        frappe.db.set_value(
            "Assessment Result",
            parent,
            "custom_total_processed_score",
            total_processed_result,
        )
        processed_percentage = (total_processed_result / total_scaled_max_score) * 100
        if (
            assessment_group_doc.custom_process_passing
            and processed_percentage >= assessment_group_doc.custom_passing_percentage
        ):

            frappe.db.set_value(
                "Assessment Result",
                parent,
                "custom_passed",
                1,
            )

        frappe.db.set_value(
            "Assessment Result",
            parent,
            "custom_processed_percentage",
            0 if total_scaled_max_score == 0 else processed_percentage,
        )

        frappe.db.set_value("Assessment Result", parent, "docstatus", 1)

    for assess_plan in assessment_plans:
        plan = assess_plan.get("name")
        calculate_ranking = assess_plan.get("custom_calculate_ranks")
        if calculate_ranking:
            calculate_ordering(plan)
    frappe.msgprint(
        "Successfully Processed all the results matching the criteria provided"
    )


def cancel_submitted_atomic_exams(result_data):
    submitted_results = [
        result.get("parent") for result in result_data if result.get("docstatus") == 1
    ]
    unique_submitted_results = set(submitted_results)

    for result in unique_submitted_results:
        assess_result = frappe.get_doc("Assessment Result", result)
        assess_result.cancel()
        amended_doc = frappe.copy_doc(assess_result)
        amended_doc.amended_from = assess_result.name
        amended_doc.save()


def get_result_from_plans(assessment_plans, group_by=False, docstatus=[0, 1]):
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")

    plans = [plan.get("name") for plan in assessment_plans]

    query = (
        frappe.qb.from_(assess_res_qb)
        .inner_join(assess_res_de_qb)
        .on(assess_res_de_qb.parent == assess_res_qb.name)
        .where(
            (
                (assess_res_qb.docstatus.isin(docstatus))
                & assess_res_qb.assessment_plan.isin(plans or [None])
                & (assess_res_de_qb.score.isnotnull())
            )
        )
    )

    if group_by:
        assess_group_qb = frappe.qb.DocType("Assessment Group")
        query = (
            query.inner_join(assess_group_qb)
            .on(assess_group_qb.name == assess_res_qb.assessment_group)
            .groupby(
                assess_res_qb.course,
                assess_res_qb.student,
                assess_res_de_qb.assessment_criteria,
            )
            .select(
                assess_res_qb.student,
                GROUP_CONCAT(assess_res_qb.assessment_plan).as_("assessment_plans"),
                Sum(
                    assess_res_de_qb.custom_processed_result
                    * assess_group_qb.custom_scale
                ).as_("score"),
                assess_res_qb.assessment_group,
                assess_res_qb.course,
            )
        )

    query = query.select(
        assess_res_qb.student,
        assess_res_qb.docstatus,
        assess_res_qb.assessment_plan,
        assess_res_de_qb.assessment_criteria,
        assess_res_de_qb.score,
        assess_res_de_qb.name,
        assess_res_de_qb.custom_scale,
        assess_res_de_qb.parent,
        assess_res_qb.course,
        assess_res_de_qb.maximum_score,
        assess_res_qb.custom_scoring_type,
    )

    return query.run(as_dict=True)


def calculate_ordering(assessment_plan):
    frappe.db.sql(
        """
        Update `tabAssessment Result` 
    INNER JOIN (SELECT 
        RANK() OVER (ORDER BY custom_total_processed_score DESC) AS ranking,
        name
    FROM 
        `tabAssessment Result`
    WHERE 
        assessment_plan = %(id)s
        AND docstatus = 1 AND custom_scoring_type=%(scoring_type)s) AS ranked_table ON  `tabAssessment Result`.name = ranked_table.name
SET  `tabAssessment Result`.custom_rank = ranked_table.ranking;
""",
        values={"id": assessment_plan, "scoring_type": "Marks"},
        as_dict=True,
    )


def process_composite_result(assessment_group, academic_year, program, div=None):
    assess_group = frappe.get_doc("Assessment Group", assessment_group)
    calc_exam_avg = assess_group.custom_exam_avg

    composite_exams = frappe.db.get_all(
        "Assessment Group",
        filters={"parent_assessment_group": assessment_group},
    )

    for atomic_exam in composite_exams:
        process_atomic_exam(atomic_exam.name, academic_year, program, div)

    plans = []

    for atomic_exam in composite_exams:
        plans.extend(get_all_assessment_plans(atomic_exam.name, program, div))

    all_results = get_result_from_plans(plans, calc_exam_avg)
    cancel_existing_composite_results(all_results, assessment_group)
    modified_result = {}
    for result in all_results:

        curr_car_doc_name = frappe.db.get_value(
            "Composite Assessment Result",
            {
                "assessment_group": assessment_group,
                "student": result.student,
                "docstatus": 0,
            },
        )
        combined_marks_or_grade = 0
        if not curr_car_doc_name:
            car_doc = frappe.new_doc("Composite Assessment Result")
            car_doc.student = result.student
            car_doc.assessment_group = assessment_group
            car_doc.processed_user = frappe.session.user
            car_doc.processed_time = frappe.utils.now()
            car_doc.append(
                "exams",
                {
                    "assessment_plan": result.assessment_plan or None,
                    "assessment_criteria": result.assessment_criteria or None,
                    "score": result.score,
                    "subject": result.course,
                    "assessment_group": assessment_group,
                },
            )
            doc = car_doc.save()

            modified_result[doc.name] = True
        else:

            frappe.get_doc(
                {
                    "doctype": "Composite Exam",
                    "parenttype": "Composite Assessment Result",
                    "parentfield": "exams",
                    "parent": curr_car_doc_name,
                    "subject": result.course,
                    "score": result.score,
                    "assessment_plan": result.assessment_plan or None,
                    "assessment_criteria": result.assessment_criteria or None,
                    "assessment_group": assessment_group,
                }
            ).insert(ignore_permissions=True)

            modified_result[doc.name] = True

        for parent in modified_result:

            if modified_result[parent]:
                assess_result = frappe.get_doc("Composite Assessment Result", parent)
                combined_marks_or_grade = 0
                for exam in assess_result.exams:
                    combined_marks_or_grade += exam.score
                assess_result.save()
                assess_result.submit()

        calculate_ranking_composite(assess_group)


def calculate_ranking_composite(assessment_group):
    frappe.db.sql(
        """
        Update `tabComposite Assessment Result` 
    INNER JOIN (SELECT 
        RANK() OVER (ORDER BY combined_marks_or_grade DESC) AS ranking,
        name
    FROM 
        `tabComposite Assessment Result`
    WHERE 
        assessment_group = %(id)s
        AND docstatus = 1) AS ranked_table ON  `tabComposite Assessment Result`.name = ranked_table.name
SET  `tabComposite Assessment Result`.rank = ranked_table.ranking;
""",
        values={"id": assessment_group},
        as_dict=True,
    )


def cancel_existing_composite_results(results, assessment_group):
    for result in results:
        frappe.db.set_value(
            "Composite Assessment Result",
            {
                "assessment_group": assessment_group,
                "student": result.student,
            },
            "docstatus",
            2,
        )
