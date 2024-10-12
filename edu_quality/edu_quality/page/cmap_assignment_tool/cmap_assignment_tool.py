import frappe
import json


# edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.get_divisions


@frappe.whitelist()
def get_divisions(**filters):
    program = get_program(filters.get("school"), filters.get("class"))
    print(program, filters)
    divisions = frappe.db.get_list(
        "Student Group",
        filters={"program": program, "academic_year": filters.get("academic_year")},
        fields=["student_group_name"],
    )
    print(divisions)
    return [division.get("student_group_name", "") for division in divisions]


def get_program(school, class_name):
    program = frappe.db.get_value(
        "Program",
        filters={"school": school, "program_name": class_name},
        fieldname="name",
    )
    return program


# edu_quality.edu_quality.page.cmap_assignment_tool.cmap_assignment_tool.get_cmap
@frappe.whitelist()
def get_cmap(**filters):
    cmap_assignment_table = frappe.qb.DocType("CMAP Assignment")
    cmap_table = frappe.qb.DocType("CMAP")
    item_table = frappe.qb.DocType("Item")
    division_table = frappe.qb.DocType("Student Group")
    # find cmap on the basis of the filters provided a optimziation before joining
    filtered_cmap_query = (
        frappe.qb.from_(cmap_table)
        .where(
            (cmap_table.academic_year == filters.get("academic_year"))
            & (cmap_table.subject == filters.get("subject"))
            & (cmap_table.unit == filters.get("unit"))
            & (cmap_table["class"] == filters.get("class"))
        )
        .select("*")
    )
    # find program by combination of school and class
    program = get_program(filters.get("school"), filters.get("class"))

    #  find all divisions which are created for that class for that academic year
    division_query = (
        frappe.qb.from_(division_table)
        .where(
            (division_table.program == program)
            & (division_table.academic_year == filters.get("academic_year"))
        )
        .select(
            division_table.student_group_name, division_table.name.as_("division_name")
        )
    )
    # calculate cartesian product between cmaps and divisions
    cross_cmap_div_query = (
        frappe.qb.from_(filtered_cmap_query)
        .cross_join(division_query)
        .cross()
        .select(
            filtered_cmap_query.name,
            filtered_cmap_query.plan_date,
            filtered_cmap_query.period,
            filtered_cmap_query.academic_year,
            filtered_cmap_query["class"],
            filtered_cmap_query["unit"],
            division_query.division_name,
            division_query.student_group_name,
        )
    )
    data = cross_cmap_div_query.run(as_dict=True)
    # return data
    frappe.errprint(str(data))
    final_query = (
        frappe.qb.from_(cross_cmap_div_query)
        .left_join(cmap_assignment_table)
        .on(
            (cross_cmap_div_query.name == cmap_assignment_table.parent)
            & (cross_cmap_div_query.division_name == cmap_assignment_table.division)
        )
        .select(
            cross_cmap_div_query.name,
            cross_cmap_div_query.plan_date,
            cross_cmap_div_query.period,
            cross_cmap_div_query.academic_year,
            cross_cmap_div_query["class"],
            cross_cmap_div_query["unit"],
            cross_cmap_div_query.division_name,
            cross_cmap_div_query.student_group_name,
            cmap_assignment_table.teacher,
            cmap_assignment_table.teacher,
        )
    )
    data = final_query.run(as_dict=True)
    print(data)
    # return data
    hash_map = construct_map(data)
    return hash_map


def construct_map(data):
    hash_map = {}
    for i in data:
        period = i.get("period")
        print(period)
        if period in hash_map:
            hash_map[period].append(i)
        else:
            hash_map[period] = [i]
    return hash_map


@frappe.whitelist()
def get_teachers(**filters):
    return frappe.db.get_list(
        "Instructor",
        filters={"custom_school": filters.get("school")},
        ignore_permissions=True,
    )


@frappe.whitelist()
def update_assignment(filters, cmap_data):
    filters = json.loads(filters) if isinstance(filters, str) else filters
    cmap_data = json.loads(cmap_data) if isinstance(cmap_data, str) else cmap_data
    program = get_program(filters.get("school"), filters.get("class"))
    # instructor_table = frappe.qb.DocType("Instructor")
    # instructor_log_table = frappe.qb.DocType("Instructor Log")
    # frappe.qb.from_(instructor_table).inner_join(instructor_log_table).on(
    #     instructor_log_table.parent == instructor_table.name
    # ).select("*")

    cmap_table = frappe.qb.DocType("CMAP")
    cmap_assignees = frappe.qb.DocType("CMAP Assignment")

    for period in cmap_data:
        for assignments in cmap_data[period]:
            query = (
                frappe.qb.from_(cmap_table)
                .inner_join(cmap_assignees)
                .on(cmap_table.name == cmap_assignees.parent)
                .where(
                    (cmap_table.period == period)
                    & (cmap_table.academic_year == filters.get("academic_year"))
                    & (cmap_table["class"] == filters.get("class"))
                )
                .select("*")
            )
            data = query.run(as_dict=True)
            return data
