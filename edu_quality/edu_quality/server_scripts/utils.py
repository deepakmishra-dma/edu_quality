import frappe
from frappe.utils import today
import json


def current_academic_year():
    filter = [
        ["Academic Year", "year_start_date", "<=", today()],
        ["Academic Year", "year_end_date", ">=", today()],
    ]
    if frappe.db.exists("Academic Year", filter):
        return frappe.db.get_value("Academic Year", filter)


def next_academic_year(current=None):
    if not current:
        current = current_academic_year()
    current_end_date = frappe.db.get_value("Academic Year", current, "year_end_date")
    filters = [["Academic Year", "year_start_date", ">", current_end_date]]
    if frappe.db.exists("Academic Year", filters):
        return frappe.db.get_all("Academic Year", filters, order_by="year_start_date")[
            0
        ].name


def previous_academic_year(current=None):
    if not current:
        current = current_academic_year()
    current_start_date = frappe.db.get_value(
        "Academic Year", current, "year_start_date"
    )
    filters = [["Academic Year", "year_end_date", "<=", current_start_date]]
    if frappe.db.exists("Academic Year", filters):
        return frappe.db.get_all("Academic Year", filters, order_by="year_end_date")[-1].name


def is_rolled_over(academic_year=None):
    if academic_year:
        filter = academic_year
    else:
        filter = [
            ["Academic Year", "year_start_date", "<=", today()],
            ["Academic Year", "year_end_date", ">=", today()],
        ]
    if frappe.db.exists("Academic Year", filter):
        return frappe.db.get_value("Academic Year", filter, order_by="year_start_date")


# def get_previous_class(program):
#     filters = [
#         ["Program", "school", "=", program.school],
#         ["Program", "sequence", "=", program.sequence - 1],
#     ]
#     if frappe.db.exists("Program", filters):
#         return frappe.db.get_value("Program", filters)


def next_class(program):
    filters = [
        ["Program", "school", "=", program.school],
        ["Program", "sequence", "=", program.sequence + 1],
    ]
    if frappe.db.exists("Program", filters):
        return frappe.db.get_value("Program", filters)


def get_division(group_name, academic_year, program):
    filters = [
        ["Division", "student_group_name", "=", group_name],
        ["Division", "academic_year", "=", academic_year],
        ["Division", "program", "=", program],
    ]
    if frappe.db.exists("Division", filters):
        return frappe.db.get_value("Division", filters)


def class_count_before_rollover(program_enrollment):
    previous_class = get_previous_class(program_enrollment.program)
    division_name = frappe.db.get_value(
        "Division", program_enrollment.student_group, "student_group_name"
    )
    division = get_division(
        division_name, previous_academic_year(), program_enrollment.program
    )
    filters = [
        ["Program Enrollment", "program", "=", program_enrollment.program],
        ["Program Enrollment", "academic_year", "=", previous_academic_year()],
        ["Program Enrollment", "program", "=", program_enrollment.program],
        ["Program Enrollment", "student_group", "=", division],
    ]


def mark_rolled_over(academic_year):
    if academic_year:
        frappe.db.set_value("Academic Year", academic_year, "rolled_over", 1)


def shift_reference_series(school):
    programs = frappe.get_all(
        "Program",
        filters={"school": school},
        fields=["name", "reference_series"],
        order_by="sequence",
    )
    previous_series = ""
    for i in programs:
        if previous_series:
            frappe.db.set_value("Program", i.name, "reference_series", previous_series)
        previous_series = i.reference_series
    previous_series = chr(ord(previous_series[0]) + 1) + chr(
        ord(previous_series[1]) + 1
    )
    for i in programs:
        frappe.db.set_value("Program", i.name, "reference_series", previous_series)
        break


def get_next_class(current_class):
    school, current_sequence = frappe.db.get_value(
        "Program", current_class, ["school", "sequence"]
    )
    if frappe.db.exists(
        "Program", {"school": school, "sequence": current_sequence + 1}
    ):
        return frappe.db.get_value(
            "Program", {"school": school, "sequence": current_sequence + 1}
        )
    elif frappe.db.exists("Program", {"previous_class": current_class}):
        return frappe.db.get_value("Program", {"previous_class": current_class})
    return None


@frappe.whitelist()
def projected_strength(current_class,academic_year=None):
    if not academic_year:
        academic_year = current_academic_year()
    prev_class = get_previous_class(current_class)
    count = frappe.db.count("Program Enrollment",{"program": prev_class,"academic_year":academic_year})
    next_class = get_next_class(current_class)
    strength = frappe.db.count(
        "Program Enrollment",
        {"program": current_class, "academic_year": current_academic_year()},
    )
    if next_class:
        strength += frappe.db.count(
            "Program Enrollment",
            {"program": next_class, "academic_year": next_academic_year()},
        )
    return strength


def get_previous_class(current_class):
    school, current_sequence = frappe.db.get_value(
        "Program", current_class, ["school", "sequence"]
    )
    if frappe.db.exists(
        "Program", {"school": school, "sequence": current_sequence - 1}
    ):
        return frappe.db.get_value(
            "Program", {"school": school, "sequence": current_sequence - 1}
        )
    return frappe.db.get_value("Program",current_class,"previous_class")


def calculate_strength_previous(current_class, academic_year=None):
    previous_class = get_previous_class(current_class)
    prev_academic_year = previous_academic_year(academic_year)

    prog_enroll_table = frappe.qb.DocType("Program Enrollment")
    stud_table = frappe.qb.DocType("Student")
    strength = 0

    if previous_class:
        query = (
            frappe.qb.from_(prog_enroll_table)
            .inner_join(stud_table)
            .on(prog_enroll_table.student == stud_table.name)
            .where(
                (prog_enroll_table.program == previous_class)
                & (prog_enroll_table.academic_year == prev_academic_year)
                & (stud_table.student_status.isin(["Current student", "Defaulter"]))
            )
            .select(stud_table.name)
        )
        result = query.run(as_dict=True)
        strength += len(result)
        frappe.errprint(query)



    query = (
        frappe.qb.from_(prog_enroll_table)
        .inner_join(stud_table)
        .on(prog_enroll_table.student == stud_table.name)
        .where(
            (prog_enroll_table.program == current_class)
            & (prog_enroll_table.academic_year == academic_year)
            & (stud_table.student_status.isin(["New student"]))
        )
        .select(stud_table.name)
    )
    frappe.errprint(query)
    result = query.run(as_dict=True)

    strength += len(result)
    return strength


def update_academic_year():
    """
    Updates the current and next academic year in the database.
    """
    current_year = current_academic_year()
    next_year = next_academic_year(current_year)
    previous_year = previous_academic_year(current_year)

    # Fetch all the academic years in a single call
    academic_years = frappe.get_all(
        "Academic Year",
        filters={"name": ["in", [previous_year, current_year, next_year]]},
    )

    for year in academic_years:
        year_doc = frappe.get_doc("Academic Year", year.name)
        if year.name == previous_year:
            year_doc.custom_current_academic_year = None
            year_doc.custom_next_academic_year = None
        else:
            year_doc.custom_current_academic_year = year.name == current_year
            year_doc.custom_next_academic_year = year.name == next_year
        year_doc.save()

    frappe.db.commit()


@frappe.whitelist()
def batch_filter(doctype, txt, searchfield, start, page_len, filters):
    data = frappe.db.get_all("Student Group", filters, "batch")
    data = [(i.batch, "") for i in data]
    return data


@frappe.whitelist(allow_guest=True)
def settlement_hook(**kwargs):
    try:
        frappe.logger("settlement").exception("called")
        data = frappe.parse_json(kwargs)
        doc = frappe.get_doc({"doctype": "Easebuzz Settlement Log", "data": data})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return 1
    except Exception as e:
        frappe.logger("settlement").exception(e)


@frappe.whitelist()
def email_recipients(student, case=0):
    # case 0: only student
    # case 1: only parent
    # case 3: both
    recipients = []

    if case == 0 or case == 3:
        student_email = frappe.db.get_value("Student", student, "student_email_id")
        if student_email:
            recipients.append(student_email)

    if case == 1 or case == 3:
        parent_emails = frappe.get_all(
            "Student Guardian",
            filters={"parent": student},
            fields=["guardian.email_address"],
            as_list=True,
        )
        parent_emails = [email for email in parent_emails if email]
        recipients.extend(parent_emails)

    return recipients
