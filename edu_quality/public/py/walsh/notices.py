import frappe


@frappe.whitelist()
def get_all_notices():
    user = frappe.session.user

    guardian = frappe.get_doc("Guardian", {"user": user})
    students = frappe.get_all("Student", filters={"guardian": guardian.name}, fields=["name", "first_name"])
    student_names = [s.name for s in students]

    notices = frappe.get_all("School Notice", fields="*", or_filters=[
        ["student", "in", student_names]
    ], order_by="creation desc")

    for notice in notices:
        s_first_name = ""
        for s in students:
            if s.name == notice.student:
                s_first_name = s.first_name
                break
        notice["student_first_name"] = s_first_name

    return {
        "data": notices,
        "total": len(notices),
    }


@frappe.whitelist()
def get_notice_by_id(id):
    school_notice_doc = frappe.get_doc("School Notice", id)
    if not school_notice_doc.status == 'read':
        school_notice_doc.status = 'read'
        school_notice_doc.read_at = frappe.utils.now()
        school_notice_doc.save(ignore_permissions=True)
        frappe.db.commit()
    school_notice = school_notice_doc.as_dict()
    school_notice["student_first_name"] = frappe.db.get_value("Student", school_notice.student, "first_name")
    return {
        "data": school_notice,
    }
