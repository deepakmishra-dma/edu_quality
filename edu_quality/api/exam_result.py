import frappe
from frappe.query_builder import Field
from frappe.query_builder.functions import Count, GROUP_CONCAT, Sum
from edu_quality.public.py.utils import get_div_students as get_div_stud
from nextai.funnel.custom_trigger import trigger_event


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

def get_assessment_result_of_plans(assessment_plans,docstatus=[0,1]):
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")

    plans = [plan.get("name") for plan in assessment_plans]

    query = (
        frappe.qb.from_(assess_res_qb)
     
        .where(
            (
                (assess_res_qb.docstatus.isin(docstatus))
                & assess_res_qb.assessment_plan.isin(plans or [None])
           
            )
        )
    ).select(assess_res_qb.star,assess_res_qb.name.as_("result_name"))
    return query.run(as_dict=True)
def get_assessment_plan_in_div(assessment_plan, division, students):
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")
    div_con = assess_res_qb.student_group.isnotnull()

    if division:
        if isinstance(division,list):
            div_con = assess_res_qb.student_group.isin(division)
        else:
            div_con = assess_res_qb.student_group == division

    query = (
        frappe.qb.from_(assess_res_qb)
        .inner_join(assess_res_de_qb)
        .on(assess_res_de_qb.parent == assess_res_qb.name)
        .where(
            (
                assess_res_qb.student.isin(students or [None])
                & (assess_res_qb.assessment_plan == assessment_plan)
                & (assess_res_de_qb.score.isnotnull())
                & (assess_res_qb.docstatus.isin([1, 0])) &(div_con)
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
def process_result(assessment_group, academic_year, program, division=None):
    if frappe.db.get_value("Assessment Group", assessment_group, "custom_is_composite"):
        frappe.enqueue(
            process_composite_result,
            assessment_group=assessment_group,
            academic_year=academic_year,
            program=program,
            div=division,
            queue="long",
        )
    else:
        frappe.enqueue(
            process_atomic_exam,
            assessment_group=assessment_group,
            academic_year=academic_year,
            program=program,
            div=division,
            queue="long",
        )

    frappe.db.commit()


def process_atomic_exam(assessment_group, academic_year, program, div=None):
    assessment_plans = get_all_assessment_plans(assessment_group, program, div)
    assessment_group_doc = frappe.get_doc("Assessment Group", assessment_group)
    errors = check_assessment_plan_in_group(assessment_plans)
    if errors:
        return errors

    submitted_docs = get_assessment_result_of_plans(assessment_plans,[1])

    cancel_submitted_atomic_exams(submitted_docs)
    non_submitted_docs = get_assessment_result_of_plans(assessment_plans,[0])
    student_list = []

    total_res_rows = len(non_submitted_docs)
    for idx in range(0, total_res_rows):
        result = non_submitted_docs[idx]
        assess_result = frappe.get_doc("Assessment Result", result.get("name"))
        if assess_result:
            assess_result.submit()
            student_list.append(assess_result.student)
        progress = idx * 100 // total_res_rows
        frappe.realtime.publish_progress(
            progress,
            title="Submitting Result",
            description=f"{idx}/{total_res_rows} rows processed",
        )

    assess_g_res_docs = []
    total_students = len(student_list)
    cancel_assessment_group_result(assessment_group, student_list)

    for idx in range(0, total_students):
        student = student_list[idx]
        existing_doc = frappe.db.exists(
            "Assessment Group Result",
            {
                "assessment_group": assessment_group,
                "student": student,
                "docstatus": ["in", [0, 1]],
            },
        )
        if existing_doc:
            assess_g_res_docs.append(existing_doc)
            continue

        assess_g_res = frappe.new_doc("Assessment Group Result")
        assess_g_res.student = student
        assess_g_res.assessment_group = assessment_group
        doc = assess_g_res.insert()
        assess_g_res_docs.append(doc.name)
        progress = idx * 100 // total_students
        frappe.realtime.publish_progress(
            progress,
            title="Creating Group Result",
            description=f"{idx}/{total_students} rows processed",
        )

    total_assess_g_res = len(assess_g_res_docs)
    for idx in range(0, total_assess_g_res):
        assess_g_res = assess_g_res_docs[idx]

        doc = frappe.get_doc("Assessment Group Result", assess_g_res)
        doc.results =[]
        frappe.realtime.publish_progress(
            progress,
            title="Submitting Assessment Group Result",
            description=f"{idx}/{total_assess_g_res} rows processed",
        )
        if doc:
            doc.submit()


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


def cancel_assessment_group_result(assessment_group, students_list):
    submitted_results = frappe.db.get_all(
        "Assessment Group Result",
        filters={
            "assessment_group": assessment_group,
            "student": ["in", students_list],
            "docstatus": ["in", [0, 1]],
        },
        fields=["name"],
    )

    submitted_results_name = [res.get("name") for res in submitted_results]
    for result in submitted_results_name:
        assess_result = frappe.get_doc("Assessment Group Result", result)
        assess_result.cancel()


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
        assess_res_qb.name.as_("result_name"),
        assess_res_qb.docstatus,
        assess_res_qb.assessment_plan,
        assess_res_de_qb.assessment_criteria,
        assess_res_de_qb.score,
        assess_res_de_qb.name,
        assess_res_de_qb.custom_scale,
        assess_res_de_qb.parent,
        assess_res_qb.course,
        assess_res_de_qb.maximum_score,
        assess_res_qb.maximum_score.as_("total_maximum_score"),
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




