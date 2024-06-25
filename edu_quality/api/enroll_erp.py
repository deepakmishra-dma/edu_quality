import frappe
import json

# @frappe.whitelist(allow_guest=True)
# def make_enrollment_erp(token=None, lms_id=None, refno=None,email=None):
#     try:
#         if token != "***REMOVED-TOKEN***":
#             return {"status": "Error", "msg": "Please provide the correct token."}
#         else:
#             create_mgr_log(lms_id, refno, email, "Pending")
#             return {"status": "Success", "msg": "Successfully Enrolled"}

#     except Exception as e:
#         create_mgr_log(lms_id, refno, email, "Failed", frappe.get_traceback())
#         return {"status": "Error", "msg": str(e)}


# def create_mgr_log(lms_id, refno, email, status, response=None):
#     mgr_log = frappe.get_doc(
#         {
#             "doctype": "MGR Enrollment Log",
#             "lms_id": lms_id,
#             "ref_no": refno,
#             "enrollment__status": status,
#             "responce": response or status,
#             "email": email
#         }
#     )
#     mgr_log.insert(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def make_enrollment_erp(**kwargs):
    try:
        data = kwargs
        token = data.get("token")
        if token != "***REMOVED-TOKEN***":
            return {"status": "Error", "msg": "Please provide the correct token."}
        lms_id = data.get("lms_id")
        ref_no = data.get("refno")
        email = data.get("email")
        create_mgr_log(lms_id,ref_no,email,json.dumps(data),"Pending")
        return {"status": "Success", "msg": "Successfully Enrolled"}
    except Exception as e:
        return {"status": "Error", "msg": str(e)}


def create_mgr_log(lms_id,ref_no,email,response=None,status=None):
    mgr_log = frappe.get_doc(
        {   
            "doctype": "MGR Enrollment Log",
            "lms_id": lms_id,
            "ref_no": ref_no,
            "responce": response,
            "email": email,
            "enrollment__status": status
        }
    )
    mgr_log.insert(ignore_permissions=True)
