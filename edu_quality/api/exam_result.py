import frappe


def get_div_students(division):
    data = frappe.db.get_all(
        "Program Enrollment",
        filters={"docstatus": 1, "student_group": ["in", division or [None]]},
        fields=["student_name", "name", "student"],
    )
    return [student.get("student") for student in data]


def check_assessment_plan_in_group(assessment_group, program, div):
    assess_group_qb = frappe.qb.DocType("Assessment Group")
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")
    div_query = assess_plan_qb.student_group
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
        )
        .select(assess_plan_qb.name, assess_plan_qb.student_group)
    )

    data = query.run(as_dict=True)
    all_errors = []
    for plan in data:
        div = plan.get("student_group")
        plan_name = plan.get("name")
        all_errors.append(check_assessment_plan_in_div(plan_name, div))

    return all_errors


def check_assessment_plan_in_div(division, assessment_plan):
    students = get_div_students(division)
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
            )
        )
        .select(
            assess_res_qb.student,
            assess_res_qb.assessment_plan,
            assess_res_de_qb.assessment_criteria,
            assess_res_qb.name,
            assess_res_qb.custom_is_absent,
        )
    )
    data = query.run(as_dict=True)
    return diff_students_and_results(students, data, assessment_plan)


def diff_students_and_results(students, results, assessment_plan):
    no_data_students = {}
    result_hash = {}
    errors = []
    for result in results:
        student = result.get(student)
        if result.get("score") == None:
            if no_data_students[student]:
                no_data_students[student].append(result)
            else:
                no_data_students[student] = [result]

        elif result_hash[student]:
            result_hash[student].append(result)
        else:
            result_hash[student] = [result]

    for student in students:
        if student not in result_hash and student not in no_data_students:
            errors.append(
                f"No Result Created for student {student} for assessment_plan {assessment_plan}"
            )
        elif student not in result_hash and student in no_data_students:
            errors.append(f"Data is missing for {student} in {assessment_plan}")
    return errors

@frappe.whitelist()
def process_result(assessment_group,acad_year, program, div):

    assess_group_qb = frappe.qb.DocType("Assessment Group")
    assess_plan_qb = frappe.qb.DocType("Assessment Group")


    errors = check_assessment_plan_in_group(assessment_group,program,div)
    if errors:
        return errors
    # frappe.qb.from_(assess_group_qb).inner_join(assess_plan_qb).on(assess_group_qb.name == assess_plan_qb.assessment_group)
    #        .select(assess_plan_qb.name, assess_plan_qb.student_group)
    
    pass