import frappe
import json
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.edu_quality.server_scripts.student import mark_entry
from edu_quality.public.py.utils import check_admin_roles, check_roles


# edu_quality.edu_quality.page.transport_drop_page.transport_drop_page.get_transport_data
@frappe.whitelist()
def get_transport_data(**filters):
    enrollment_table = frappe.qb.DocType("Program Enrollment")
    attendance_entry = frappe.qb.DocType("Attendance Entry")
    attendance_status = frappe.qb.DocType("Attendance Status")
    absent_and_delays = frappe.qb.DocType("Absent and Delay")
    student_table = frappe.qb.DocType("Student")

    today = frappe.utils.today()
    academic_year = current_academic_year()
    user_roles = frappe.get_roles(frappe.session.user)

    if check_roles(user_roles, ["Transporter"]):
        school = [
            frappe.db.get_value(
                "Transporter School Assignment",
                filters={"user": frappe.session.user},
                fieldname="parent",
            )
            or None
        ]
    if check_admin_roles(user_roles):
        school = frappe.db.get_all("School")
    schools = [i.get("name") for i in school]
    query = (
        frappe.qb.from_(student_table)
        .inner_join(enrollment_table)
        .on(student_table.name == enrollment_table.student)
        .left_join(attendance_entry)
        .on(student_table.name == attendance_entry.student)
        .left_join(absent_and_delays)
        .on(attendance_entry.name == absent_and_delays.parent)
        .left_join(attendance_status)
        .on(attendance_entry.status == attendance_status.name)
        .where(
            (enrollment_table.docstatus == 1)
            & (enrollment_table.custom_school.isin(schools))
            & (student_table.bus_service_required == 1)
            & (student_table.drop_bus == filters.get("bus_no"))
            & (enrollment_table.academic_year == academic_year)
            & ((attendance_entry.date == today) | (attendance_entry.date == None))
        )
        .select(
            student_table.name.as_("student_id"),
            student_table.student_name,
            student_table.drop_address,
            student_table.image,
            attendance_status.type,
            attendance_entry.name.as_("attendance_id"),
            attendance_entry.status,
            absent_and_delays.status.as_("drop_status"),
        )
    )

    return calculate_status(query.run(as_dict=True))


def calculate_status(transport_data):
    for student in transport_data:
        status_type = student.get("type")
        drop_status = student.get("drop_status")

        if drop_status == "early_pickup":
            student["drop_type"] = "early_pickup"
        elif drop_status == "late_drop":
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
    mark_entry(id, message, "onboard")


# edu_quality.edu_quality.page.transport_drop_page.transport_drop_page.update_qr
@frappe.whitelist()
def update_qr(acad, ref, school):
    prefix = frappe.db.get_value("School", filters={"name": school}, fieldname="prefix")
    student = prefix + ref
    mark_entry(
        student, "Onboard marked with qrcode scan on drop transport page", "onboard"
    )
