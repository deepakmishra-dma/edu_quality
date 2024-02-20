import frappe
from frappe.utils.background_jobs import get_jobs

def set_progress(current, total,db, job, expires_in_sec=300):
    progress = (current / total) * 100
    progress = f"{progress:.2f}%"
    frappe.cache().set_value(
        "student_import_status",
        {"progress": progress, "job": job,"db":db},
        expires_in_sec=expires_in_sec,
    )
    frappe.db.commit()

@frappe.whitelist()
def get_migration_progress():
    student_import_status = frappe.cache().get_value("student_import_status")
    if not student_import_status and is_migration_jobs_queued():
        student_import_status = {
            "progress": "Background Jobs Queued. Please be patient while it's processed.", 
            "job": None,
        }

    return student_import_status or {}

def is_migration_jobs_queued():
    jobs = get_jobs(site=frappe.local.site, key="job_name")[frappe.local.site]

    return any("student_import_" in job for job in jobs)  # noqa: 501