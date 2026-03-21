import frappe

from edu_quality.edu_quality.server_scripts.student import mark_entry
from frappe.query_builder import Order
from datetime import datetime

from edu_quality.edu_quality.doctype.student_attendance_sheet.student_attendance_sheet import (
    get_holidays,
)


@frappe.whitelist()
def add_leave_note(note, status, student, dates, program, start_date, end_date):

    holidays = get_holidays(start_date, end_date, program, True)

    for date in dates:
        date_obj = datetime.strptime(str(date), "%Y-%m-%d").date()
        if date_obj in holidays:
            continue

        mark_entry(student, "absent", note, date)
    return {
        "success": True,
        "message": "Note Saved",
    }


@frappe.whitelist()
def add_early_pick_up(
    status,
    student,
    date,
    time,
    program,
    note=None,
):
    date_obj = datetime.strptime(str(date), "%Y-%m-%d").date()

    holidays = get_holidays(date, date, program, True)

    if date_obj in holidays:
        return {
            "success": False,
            "message": "Date Picked is an Holiday",
        }
    mark_entry(student, status, note, date, time)

    return {
        "success": True,
        "message": "Note Saved",
    }


@frappe.whitelist()
def get_past_pick_ups(student):
    ae_qb = frappe.qb.DocType("Attendance Entry")
    ad_qb = frappe.qb.DocType("Absent and Delay")

    query = (
        frappe.qb.from_(ae_qb)
        .inner_join(ad_qb)
        .on((ae_qb.name == ad_qb.parent) & (student == ae_qb.student))
        .where(ad_qb.status.isin(["absent", "sick", "leave"]))
        .orderby(ae_qb.date, order=Order.desc)
        .select(
            ad_qb.reason,
            ae_qb.date,
        )
    )
    results = query.run(as_dict=True)
    for result in results:
        if result["date"]:
            date_obj = datetime.strptime(str(result["date"]), "%Y-%m-%d")
            result["date"] = date_obj.strftime("%d/%m/%y")
    return results
