import frappe

from edu_quality.edu_quality.server_scripts.student import mark_entry


@frappe.whitelist()
def add_leave_note(note, status, student, dates):
    for date in dates:
        mark_entry(student, "absent", note, date)
    return {
        "success": True,
        "message": "Note Saved",
    }


@frappe.whitelist()
def add_early_pick_up(status, student, dates, time, note=None):
    for date in dates:
        mark_entry(student, status, note, date, time)
    return {
        "success": True,
        "message": "Note Saved",
    }
