import frappe
import json
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.edu_quality.server_scripts.student import mark_entry
from edu_quality.public.py.utils import check_admin_roles, check_roles
from frappe.query_builder import Order


# edu_quality.edu_quality.page.transport_drop_page.transport_drop_page.get_transport_data
@frappe.whitelist()
def get_transport_data(**filters):
    enrollment_table = frappe.qb.DocType("Program Enrollment")
    attendance_entry = frappe.qb.DocType("Attendance Entry")
    attendance_status = frappe.qb.DocType("Attendance Status")
    absent_and_delays = frappe.qb.DocType("Absent and Delay")
    student_table = frappe.qb.DocType("Student")

    today = frappe.utils.today()
    academic_year = frappe.db.get_value(
        "Academic Year", filters={"custom_current_academic_year": 1}, fieldname="name"
    )
    schools = get_current_school()

    query = (
        frappe.qb.from_(student_table)
        .inner_join(enrollment_table)
        .on(student_table.name == enrollment_table.student)
        .left_join(attendance_entry)
        .on(
            (student_table.name == attendance_entry.student)
            & (attendance_entry.date == today)
        )
        .left_join(attendance_status)
        .on(attendance_entry.status == attendance_status.name)
        .where(
            (enrollment_table.docstatus == 1)
            & (enrollment_table.custom_school.isin(schools))
            & (student_table.bus_service_required == 1)
            & (student_table.drop_bus == filters.get("bus_no"))
            & (enrollment_table.academic_year == academic_year)
            & (student_table.student_status.isin(["Current student", "Defaulter"]))
            # & ((attendance_entry.date == today) | (attendance_entry.name.isnull()))
        )
        .select(
            student_table.name.as_("student_id"),
            student_table.student_name,
            student_table.drop_address,
            student_table.image,
            attendance_status.type,
            attendance_entry.name.as_("attendance_id"),
            attendance_entry.status,
        )
    )

    result = query.run(as_dict=True)
    attendance_ids = [i.get("attendance_id") for i in result]

    absentees_query = (
        frappe.qb.from_(absent_and_delays)
        .inner_join(attendance_entry)
        .on(absent_and_delays.parent == attendance_entry.name)
        .where(absent_and_delays.parent.isin(attendance_ids or [None]))
        .orderby(absent_and_delays.creation, Order.desc)
    ).select(
        absent_and_delays.timestamp.as_("creation"),
        absent_and_delays.status.as_("drop_status"),
        attendance_entry.student.as_("student_id"),
    )

    absentees_query_result = absentees_query.run(as_dict=True)
    absentees_hash = calculate_hash(absentees_query_result)
    return calculate_status(query.run(as_dict=True), absentees_hash)


# calculate hash to count most recent status only in absentees table
def calculate_hash(absentees_query_result):
    hash = {}
    for i in absentees_query_result:
        student_id = i.get("student_id")
        creation = i.get("creation")
        drop_status = i.get("drop_status")

        if student_id not in hash:
            hash[student_id] = i
        else:
            if creation > hash[student_id]["creation"]:
                hash[student_id]["drop_status"] = drop_status
    return hash


def calculate_status(transport_data, absentees_hash):
    for student in transport_data:
        status_type = student.get("type")
        student_id = student.get("student_id")
        drop_status = absentees_hash.get(student_id, student).get("drop_status")

        if drop_status == "early_pickup" or drop_status == "Early Pickup":
            student["drop_type"] = "early_pickup"
        elif drop_status == "late_drop" or drop_status == "Late Drop":
            student["drop_type"] = "late_drop"
        elif drop_status == "onboard":
            student["drop_type"] = "onboard"
        elif "absent" in str(drop_status) or (
            status_type and status_type.lower() == "absent"
        ):
            student["drop_type"] = "absent"
        else:
            student["drop_type"] = None

    return transport_data


# edu_quality.edu_quality.page.transport_drop_page.transport_drop_page.update
@frappe.whitelist()
def update(id, message):
    mark_entry(id, "onboard", message)


# edu_quality.edu_quality.page.transport_drop_page.transport_drop_page.update_qr
@frappe.whitelist()
def update_qr(acad=None, ref=None, school=None):
    prefix = frappe.db.get_value("School", filters={"name": school}, fieldname="prefix")

    student = f"{prefix}{ref}"
    if not school and not acad:
        student = ref

    mark_entry(
        student, "onboard", "Onboard marked with qrcode scan on drop transport page"
    )


@frappe.whitelist()
def get_current_school():
    user_roles = frappe.get_roles(frappe.session.user)
    if check_roles(user_roles, ["Transporter"]):
        school = [
            frappe.db.get_value(
                "Transporter School Assignment",
                filters={"user": frappe.session.user},
                fieldname="parent",
            )
        ]

    if check_admin_roles(user_roles):
        school = frappe.db.get_all("School")
    schools = [i.get("name") if isinstance(i, dict) else i for i in school]
    return schools
