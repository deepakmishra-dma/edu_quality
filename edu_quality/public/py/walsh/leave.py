import frappe


@frappe.whitelist()
def add_leave_note(note, type, student, dates):
    # student_doc = frappe.get_cached_doc("Student", student)
    enrollment = frappe.get_cached_doc("Program Enrollment", {"student": student})
    division = enrollment.student_group
    class_name = enrollment.program
    print(note, type, student, dates, division, class_name)
    for date in dates:
        entry_id_values = {
            "student": student,
            "division": division,
            "class": class_name,
            "date": date
        }
        entry = (
            frappe.get_doc("Attendance Entry", entry_id_values)
            if frappe.db.exists("Attendance Entry", entry_id_values)
            else frappe.new_doc("Attendance Entry")
        )
        entry.update(entry_id_values)
        absent_and_delays = entry.absent_and_delays or []
        absent_and_delays.append({
            "reason": note,
            "status": "absent_for_" + type,
            "timestamp": frappe.utils.get_datetime()
        })
        entry.update({
            "absent_and_delays": absent_and_delays,
            "status": entry.status or "absent"
        })
        entry.save(ignore_permissions=True)
    return {
        "success": True,
        "message": "Note Saved",
    }
