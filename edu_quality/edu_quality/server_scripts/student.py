import frappe

from frappe.utils import getdate
import datetime


@frappe.whitelist()
def mark_entry(student, status, reason=None, date=None, time=None):
    if not date:
        date = getdate()
    if not time:
        time = datetime.datetime.now().strftime("%H:%M:%S")

    try:
        if frappe.db.exists("Attendance Entry", {"student": student, "date": date}):
            entry = frappe.get_doc(
                "Attendance Entry", {"student": student, "date": date}
            )
            entry.append(
                "absent_and_delays",
                {
                    "reason": reason,
                    "status": status,
                    "timestamp": date + " " + time,
                    "user": frappe.session.user,
                },
            )
            entry.flags.ignore_mandatory = True
            entry.save(ignore_permissions=True)
        else:
            entry = frappe.new_doc("Attendance Entry")
            entry.student = student
            entry.date = date
            entry.append(
                "absent_and_delays",
                {
                    "reason": reason,
                    "status": status,
                    "timestamp": date + " " + time,
                    "user": frappe.session.user,
                },
            )
            entry.insert(ignore_permissions=True)
        return True
    except Exception as e:
        frappe.logger("entry").exception(e)
        return False
