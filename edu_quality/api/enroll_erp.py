import frappe
from edu_quality.public.py.application import enroll_student


@frappe.whitelist(allow_guest=True)
def make_enrollment_erp(token=None, lms_id=None, refno=None):
    try:
        if token != "***REMOVED-TOKEN***":
            return {"status": "Error", "msg": "Please provide the correct token."}

        student_applicant = frappe.get_value("Student Applicant", {"lms_id": lms_id})
        if student_applicant:
            application_status = frappe.get_value(
                "Student Applicant", student_applicant, "application_status"
            )
            if application_status == "Admitted":
                create_mgr_log(lms_id, refno, "Failed", "Student already enrolled")
                return {"status": "Error", "msg": "Student already enrolled"}

            enroll_student(student_applicant, refno)
            create_mgr_log(lms_id, refno, "Success")
            return {"status": "Success", "msg": "Successfully Enrolled"}
        else:
            create_mgr_log(lms_id, refno, "Failed", "Student Applicant not found")
            return {"status": "Error", "msg": "Student Applicant not found"}

    except Exception as e:
        create_mgr_log(lms_id, refno, "Failed", frappe.get_traceback())
        return {"status": "Error", "msg": str(e)}


def create_mgr_log(lms_id, refno, status, response=None):
    mgr_log = frappe.get_doc(
        {
            "doctype": "MGR Enrollment Log",
            "lms_id": lms_id,
            "ref_no": refno,
            "enrollment__status": status,
            "responce": response or status,
        }
    )
    mgr_log.insert(ignore_permissions=True)
