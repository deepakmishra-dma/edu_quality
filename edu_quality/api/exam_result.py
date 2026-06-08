import frappe
from frappe.query_builder import Field
from frappe.query_builder.functions import Count, GROUP_CONCAT, Sum
from edu_quality.public.py.utils import get_div_students as get_div_stud


# from nextai.funnel.custom_trigger import trigger_event
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


def get_div_students(division):
    data = get_div_stud(division)
    return [student.get("student") for student in data]


def get_all_assessment_plans(assessment_group, program, div):
    assess_group_qb = frappe.qb.DocType("Assessment Group")
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")

    div_query = assess_plan_qb.student_group.isnotnull()

    if div and isinstance(div, list):
        div_query = assess_plan_qb.student_group.isin(div)
    elif div:
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
            # assess_plan_qb.custom_calculate_ranks,
            assess_plan_qb.student_group,
            assess_plan_qb.custom_scoring_type,
            assess_plan_qb.course,
        )
    )

    data = query.run(as_dict=True)

    return data


def check_assessment_plan_in_group(assessment_plans, student_master=None):
    all_errors = []
    already_submitted = []
    for plan in assessment_plans:
        div = plan.get("student_group")
        plan_name = plan.get("name")
        errors = check_assessment_plan_in_div(plan_name, div, student_master)
        all_errors.extend(errors)

    if already_submitted:
        frappe.prompt("There are submitted results already, proceed ?")
    if all_errors:
        frappe.log_error("Error while checking plans in group", str(all_errors))
    return all_errors


def get_student_con(student_master=None, qb=None):
    if student_master and len(student_master):
        return qb.student.isin(student_master)
    else:
        return qb.student.isnotnull()


def get_assessment_result_of_plans(
    assessment_plans, docstatus=[0, 1], student_master=None
):
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")
    student_con = get_student_con(student_master, assess_res_qb)
    plans = [plan.get("name") for plan in assessment_plans]

    query = (
        frappe.qb.from_(assess_res_qb).where(
            (
                (assess_res_qb.docstatus.isin(docstatus))
                & assess_res_qb.assessment_plan.isin(plans or [None])
                & (student_con)
            )
        )
    ).select(assess_res_qb.star, assess_res_qb.name.as_("result_name"))
    return query.run(as_dict=True)


def get_assessment_res_in_div(assessment_plan, division, students):
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")
    div_con = assess_res_qb.student_group.isnotnull()

    if division:
        if isinstance(division, list):
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
                & (assess_res_qb.docstatus.isin([1, 0]))
                & (div_con)
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


def check_assessment_plan_in_div(assessment_plan, division, student_master=None):
    if not student_master or not len(student_master):
        students = get_div_students(division)
    else:
        students = [s for s in student_master if s in get_div_students(division)]

    data = get_assessment_res_in_div(assessment_plan, division, students)

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


def get_all_divisions_of_students(students, academic_year):
    data = frappe.db.get_all(
        "Program Enrollment",
        filters={
            "student": ["in", students],
            "academic_year": academic_year,
            "docstatus": 1,
        },
        fields=["student_group"],
    )
    return {d.student_group for d in data}


@frappe.whitelist()
def process_result(
    assessment_group,
    academic_year,
    program,
    division=None,
    ref_nos=None,
    create_toppers_only=False,
):
    is_composite, school = frappe.db.get_value(
        "Assessment Group", assessment_group, ["custom_is_composite", "custom_school"]
    )
    student_list = get_ref_nos_from_string(ref_nos, school) if ref_nos else []
    divisions = get_all_divisions_of_students(student_list, academic_year)
    if is_composite:
        frappe.enqueue(
            process_composite_result,
            assessment_group=assessment_group,
            academic_year=academic_year,
            program=program,
            div=division or divisions,
            student_master=student_list,
            create_toppers_only=create_toppers_only,
            queue="long",
        )
    else:
        frappe.enqueue(
            process_atomic_exam,
            assessment_group=assessment_group,
            academic_year=academic_year,
            program=program,
            div=division or divisions,
            student_master=student_list,
            create_toppers_only=create_toppers_only,
            queue="long",
            timeout=15000,
        )

    frappe.db.commit()


def process_atomic_exam(
    assessment_group,
    academic_year,
    program,
    div=None,
    student_master=None,
    create_toppers_only=False,
):

    _process_atomic_exam(
        assessment_group=assessment_group,
        academic_year=academic_year,
        program=program,
        div=div,
        student_master=student_master,
        create_toppers_only=create_toppers_only,

    )


def _process_atomic_exam(
    assessment_group,
    academic_year,
    program,
    div=None,
    student_master=None,
    create_toppers_only=False,
):

    assessment_plans = get_all_assessment_plans(assessment_group, program, div)

    errors = check_assessment_plan_in_group(assessment_plans, student_master)
    if errors:
        return

    if not int(create_toppers_only):
        process_assessment_results(assessment_plans, student_master)

    student_list = create_assessment_group_results(assessment_group, assessment_plans)
    calculate_and_save_group_results(assessment_group, student_list)
    process_toppers(
        assessment_group, assessment_plans, get_division_set(assessment_plans)
    )

    frappe.msgprint(
        "Successfully Processed all the results matching the criteria provided"
    )
    # except Exception as e:
    #     handle_error()


def get_division_set(assessment_plans):
    return set(plan.get("student_group") for plan in assessment_plans)


def get_subject_set(assessment_plans):
    return set(
        plan.get("course")
        for plan in assessment_plans
        if plan.get("custom_scoring_type").lower() == "marks"
    )


def process_assessment_results(assessment_plans, student_master):
    submitted_docs = get_assessment_result_of_plans(
        assessment_plans, [1], student_master
    )
    cancel_submitted_atomic_exams(submitted_docs)
    non_submitted_docs = get_assessment_result_of_plans(
        assessment_plans, [0], student_master
    )
    print(submitted_docs)
    submit_assessment_results(non_submitted_docs)


def submit_assessment_results(non_submitted_docs):
    total_res_rows = len(non_submitted_docs)
    print(non_submitted_docs, "hhhe")
    for idx, result in enumerate(non_submitted_docs):
        # frappe.db.begin()
        assess_result = frappe.get_cached_doc("Assessment Result", result.get("name"))
        if assess_result:
            assess_result.submit()
        progress = idx * 100 // total_res_rows
        frappe.publish_progress(
            progress,
            title="Submitting Result",
            description=f"{idx}/{total_res_rows} rows processed",
        )
        # frappe.db.commit()


def create_assessment_group_results(assessment_group, assessment_plans):
    plans = [plan.get("name") for plan in assessment_plans]

    student_set = get_student_set(plans)
    student_list = list(student_set)
    total_students = len(student_list)
    for idx, student in enumerate(student_list):
        # frappe.db.begin()
        create_or_get_assessment_group_result(assessment_group, student)
        progress = (idx // total_students) * 100
        frappe.publish_progress(
            progress,
            title="Creating Group Result",
            description=f"{idx}/{total_students} rows processed",
        )
        frappe.db.commit()
    return student_list


def get_student_set(assessment_plans):
    student_set = set()
    all_students = frappe.get_all(
        "Assessment Result",
        filters={
            "assessment_plan": ["in", assessment_plans],
            "docstatus": ["in", [0, 1]],
        },
        fields=["student"],
    )

    student_set.update(result.student for result in all_students)
    return student_set


def create_or_get_assessment_group_result(assessment_group, student):
    existing_doc = frappe.db.exists(
        "Assessment Group Result",
        {
            "assessment_group": assessment_group,
            "student": student,
            "docstatus": ["in", [0]],
        },
    )
    if existing_doc:
        return existing_doc
    assessment_group_doc = frappe.get_cached_doc("Assessment Group", assessment_group)
    assess_g_res = frappe.new_doc("Assessment Group Result")
    assess_g_res.student = student
    assess_g_res.program = assessment_group_doc.custom_program
    assess_g_res.assessment_group = assessment_group
    doc = assess_g_res.insert()
    return doc.name


def calculate_and_save_group_results(assessment_group, student_list):
    assess_g_res_docs = [
        frappe.db.exists(
            "Assessment Group Result",
            {
                "assessment_group": assessment_group,
                "student": student,
                "docstatus": ["in", [0]],
            },
        )
        for student in student_list
    ]
    asses_g_doc = frappe.get_cached_doc("Assessment Group", assessment_group)
    assess_g_res_docs = [doc for doc in assess_g_res_docs if doc]
    total_assess_g_res = len(assess_g_res_docs)
    students_to_ignore = asses_g_doc.get_student_with_online_submission()
    for idx, assess_g_res in enumerate(assess_g_res_docs):
        assess_g_r_doc = frappe.get_cached_doc("Assessment Group Result", assess_g_res)
        if assess_g_r_doc:
            assess_g_r_doc.calculate_total_score()
            if assess_g_r_doc.student in students_to_ignore:
                assess_g_r_doc.online_assessment = 1
            assess_g_r_doc.save()

    group_class_ranks = asses_g_doc.get_group_class_rank()
    group_div_ranks = asses_g_doc.get_group_div_rank()

    for idx, assess_g_res in enumerate(assess_g_res_docs):
        assess_g_r_doc = frappe.get_cached_doc("Assessment Group Result", assess_g_res)
        if assess_g_r_doc:
            if assess_g_res in group_class_ranks:
                frappe.db.set_value(
                    "Assessment Group Result",
                    assess_g_res,
                    "class_rank",
                    group_class_ranks[assess_g_res],
                )
            if assess_g_res in group_div_ranks:
                frappe.db.set_value(
                    "Assessment Group Result",
                    assess_g_res,
                    "division_rank",
                    group_div_ranks[assess_g_res],
                )

        frappe.publish_progress(
            idx * 100 // total_assess_g_res,
            title="Saving Assessment Group Result",
            description=f"{idx}/{total_assess_g_res} rows processed",
        )


def handle_error():
    frappe.db.rollback()
    frappe.log_error(
        title="Error in processing atomic exam",
        message=frappe.get_traceback(),
    )
    frappe.msgprint(
        "Error in processing atomic exam. Please check the logs for more details"
    )


def process_toppers(assessment_group, assessment_plans, division_set=None):
    assessment_group_doc = frappe.get_cached_doc("Assessment Group", assessment_group)
    assessment_group_doc.delete_topper_events()

    assessment_group_doc.create_class_topper()
    assessment_group_doc.create_division_toppers(division_set)
    assessment_group_doc.create_subject_toppers()


def get_ref_nos_from_string(data, school):
    ref_nos = data.split(",")

    student_doc_names = []
    if not any(ref_nos):
        return

    for ref_no in ref_nos:
        if not ref_no:
            continue

        student = frappe.db.exists("Student", {"name": ref_no}) or frappe.db.exists(
            "Student", {"reference_number": ref_no, "school": school}
        )
        if not student:
            frappe.throw(
                f"Cannot find studenf for the specified reference number {ref_no} with school {school}"
            )

        student_doc_names.append(student)
    return student_doc_names


def cancel_submitted_atomic_exams(result_data):
    submitted_results = [
        result.get("name") for result in result_data if result.get("docstatus") == 1
    ]
    unique_submitted_results = set(submitted_results)

    for result in unique_submitted_results:
        # frappe.db.begin()
        assess_result = frappe.get_cached_doc("Assessment Result", result)
        amended_doc = frappe.copy_doc(assess_result)
        amended_doc.docstatus = 0
        amended_doc.amended_from = assess_result.name
        assess_result.cancel()

        amended_doc.save()
        # frappe.db.commit()


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
        assess_result = frappe.get_cached_doc("Assessment Group Result", result)
        if assess_result.docstatus == 1:
            assess_result.cancel()


def get_result_from_plans(
    assessment_plans, group_by=False, docstatus=[0, 1], student_master=None
):
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")
    student_con = get_student_con(student_master, assess_res_qb)
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
                & (student_con)
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


def process_composite_result(
    assessment_group, academic_year, program, div=None, student_master=None
):
    assess_group = frappe.get_cached_doc("Assessment Group", assessment_group)
    calc_exam_avg = assess_group.custom_exam_avg

    composite_exams = frappe.db.get_all(
        "Assessment Group",
        filters={"parent_assessment_group": assessment_group},
    )

    for atomic_exam in composite_exams:
        process_atomic_exam(
            atomic_exam.name, academic_year, program, div, student_master
        )

    plans = []

    for atomic_exam in composite_exams:
        plans.extend(get_all_assessment_plans(atomic_exam.name, program, div))

    all_results = get_result_from_plans(plans, calc_exam_avg, student_master)
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
                assess_result = frappe.get_cached_doc(
                    "Composite Assessment Result", parent
                )
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
