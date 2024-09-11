import frappe


@frappe.whitelist()
def get_all_notices():
    user = frappe.session.user
    if user == "Administrator":
        all_notices = frappe.get_all("School Notice", fields=[
            "type_of_notifications", "subject", "name", "creation", "notice"
        ])
        return {
            "data": all_notices,
            "total": len(all_notices),
        }

    guardian = frappe.get_doc("Guardian", {"user": user})
    students = frappe.get_all("Student", filters={"guardian": guardian.name}, fields=["name", "first_name"])
    student_names = [s.name for s in students]

    student_select = frappe.get_all("Student Select",
                                    filters=[["parenttype", "=", "School Notice"], ["student", "in", student_names]],
                                    fields=["parent", "student"])
    notice_names = [ss.parent for ss in student_select]
    notices = frappe.get_all("School Notice", fields="*", or_filters=[
        ["type_of_notifications", '=', "Everyone"],
        ["name", "in", notice_names]
    ])

    for notice in notices:
        for ss in student_select:
            if notice.name == ss.parent:
                student_first_name = None
                for s in students:
                    if s.name == ss.student:
                        student_first_name = s.first_name
                if notice.get("students"):
                    notice["students"].append(student_first_name)
                else:
                    notice["students"] = [student_first_name]

        if notice.get("students"):
            if len(list(set(notice["students"]))) == len(students):
                notice["students"] = []

    return {
        "data": notices,
        "total": len(notices),
    }

    # get schools
    # get classes
    # get divisions
    # return notices for all above with mentioned student


@frappe.whitelist()
def get_notice_by_id(id):
    school_notice = frappe.get_doc("School Notice", id).as_dict()
    student_selects = school_notice.students
    student_names = [s.student for s in student_selects]
    students = frappe.get_all("Student", filters={"name": ["in", student_names]}, fields=["name", "first_name"])
    school_notice["students"] = [s.first_name for s in students]
    return {
        "data": school_notice,
    }
