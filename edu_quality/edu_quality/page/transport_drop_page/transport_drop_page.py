import frappe
import json
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


# edu_quality.edu_quality.page.transport_drop_page.transport_drop_page.get_transport_data
@frappe.whitelist()
def get_transport_data(**filters):
    enrollment_table = frappe.qb.DocType("Program Enrollment")
    attendance_entry = frappe.qb.DocType("Attendance Entry")
    attendance_status = frappe.qb.DocType("Attendance Status")

    today = frappe.utils.today()
    academic_year = current_academic_year()
    frappe.errprint(filters)
    query = (
        frappe.qb.from_(enrollment_table)
        .inner_join(attendance_entry)
        .on(enrollment_table.name == attendance_entry.program_enrollment)
        .inner_join(attendance_status)
        .on(attendance_entry.status == attendance_status.name)
        .where(
            (enrollment_table.docstatus == 1)
            & (enrollment_table.transport_service_required == 1)
            & (enrollment_table.drop_bus == filters.get("bus_no"))
            & (enrollment_table.academic_year == academic_year)
            & (attendance_entry.date == today)
        )
        .select(
            enrollment_table.name,
            enrollment_table.student,
            enrollment_table.student_name,
            enrollment_table.drop_address,
            enrollment_table.image,
            attendance_entry.late_drop,
            attendance_status.type,
            attendance_entry.early_pickup,
            attendance_entry.drop,
            attendance_entry.onboard,
            attendance_entry.name.as_("attendance_id"),
        )
    )
    return calculate_status(query.run(as_dict=True))


def calculate_status(transport_data):
    for student in transport_data:
        status_type = student.get("type")
        late_drop = student.get("late_drop")
        onboard = student.get("onboard")
        early_pickup = student.get("early_pickup")

        if early_pickup:
            student["drop_type"] = "early_pickup"
        elif late_drop:
            student["drop_type"] = "late_drop"
        elif onboard:
            student["drop_type"] = "onboard"
        elif status_type and status_type.lower() == "absent":
            student["drop_type"] = "absent"
        else:
            student["drop_type"] = None

    return transport_data


# edu_quality.edu_quality.page.transport_drop_page.transport_drop_page.update
@frappe.whitelist()
def update(id):
    attendance = frappe.get_doc("Attendance Entry", id)

    attendance.onboard = frappe.utils.now()
    attendance.save()
