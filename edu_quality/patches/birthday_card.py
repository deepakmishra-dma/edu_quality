import frappe
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
all_program_enrollments = frappe.db.get_all(
    "Program Enrollment", {"academic_year": current_academic_year()}
)

for i in all_program_enrollments:
    if not frappe.db.exists("Birthday Card", {"program_enrollment", i.get("name")}):
        frappe.get_doc(
            {"doctype": "Birthday Card", "program_enrollment": i.get("name")}
        ).insert(ignore_permissions=True)
