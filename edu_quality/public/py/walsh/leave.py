import frappe

from edu_quality.edu_quality.server_scripts.student import mark_entry


@frappe.whitelist()
def add_leave_note(note, status, student, dates):
    print(dates)
    for date in dates:
        mark_entry(student, "absent_for_" + status, note, date)
        # entry_id_values = {
        #     "student": student,
        #     "date": date
        # }
        # entry = (
        #     frappe.get_doc("Attendance Entry", entry_id_values)
        #     if frappe.db.exists("Attendance Entry", entry_id_values)
        #     else frappe.new_doc("Attendance Entry")
        # )
        # entry.update(entry_id_values)
        # absent_and_delays = entry.absent_and_delays or []
        # absent_and_delays.append({
        #     "reason": note,
        #     "status": "absent_for_" + status,
        #     "timestamp": frappe.utils.get_datetime()
        # })
        # entry.update({
        #     "absent_and_delays": absent_and_delays
        # })
        # entry.save(ignore_permissions=True)
    return {
        "success": True,
        "message": "Note Saved",
    }
