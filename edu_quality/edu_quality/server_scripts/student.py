import frappe
from frappe.utils import getdate


@frappe.whitelist()
def mark_entry(student, status, reason=None, date=None):
    if not date:
        date = getdate()
    print(date)
    try:
        if frappe.db.exists("Attendance Entry", {"student": student, "date": date}):
            entry = frappe.get_doc("Attendance Entry", {"student": student, "date": date})
            entry.append("absent_and_delays", {
                "reason": reason,
                "status": status,
                "timestamp": frappe.utils.now()
            })
            entry.save(ignore_permissions=True)
        else:
            entry = frappe.new_doc("Attendance Entry")
            entry.student = student
            entry.date = date
            entry.append("absent_and_delays", {
                "reason": reason,
                "status": status,
                "timestamp": frappe.utils.now()
            })
            entry.insert(ignore_permissions=True)
        return True
    except Exception as e:
        frappe.logger('entry').exception(e)
        return False
