import frappe


@frappe.whitelist(allow_guest=True)
def make_enrollment_erp(token=None, lms_id=None, refno=None,email=None):
    try:
        if token != "***REMOVED-TOKEN***":
            return {"status": "Error", "msg": "Please provide the correct token."}
        else:
            create_mgr_log(lms_id, refno, email, "Pending")
            return {"status": "Success", "msg": "Successfully Enrolled"}

    except Exception as e:
        create_mgr_log(lms_id, refno, email, "Failed", frappe.get_traceback())
        return {"status": "Error", "msg": str(e)}


def create_mgr_log(lms_id, refno, email, status, response=None):
    mgr_log = frappe.get_doc(
        {
            "doctype": "MGR Enrollment Log",
            "lms_id": lms_id,
            "ref_no": refno,
            "enrollment__status": status,
            "responce": response or status,
            "email": email
        }
    )
    mgr_log.insert(ignore_permissions=True)
