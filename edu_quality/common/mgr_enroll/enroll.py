import frappe

@frappe.whitelist(allow_guest=True)
def make_enrollment_erp(token=None,lms_id=None,refno=None):
    if token!="***REMOVED-TOKEN***":
        return {"status":"Error","msg":"Please pass correct token"}
    else:
        pass