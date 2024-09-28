import frappe

from edu_quality.public.py.walsh.admin import render_jinja


@frappe.whitelist()
def get_students():
    user = frappe.session.user
    guardian = frappe.get_doc("Guardian", {"user": user})
    students = frappe.get_all("Student", filters={"guardian": guardian.name}, fields=["*"])
    return students


@frappe.whitelist()
def get_all_notices(page=1, limit=0):
    if page:
        page = int(page)
    if limit:
        limit = int(limit)
    if not limit:
        limit = 1000
    user = frappe.session.user

    guardian = frappe.get_doc("Guardian", {"user": user})
    students = frappe.get_all("Student", filters={"guardian": guardian.name}, fields=["*"])
    student_dict = {s.name: s for s in students}
    student_names = [s.name for s in students]

    enrollments_values = {
        'student_names': student_names,
    }

    enrollments = frappe.db.sql('''
        select name, custom_school, academic_year, student, student_group, program
        from `tabProgram Enrollment`
        where student in %(student_names)s
        group by custom_school, academic_year, student, student_group, program;
    ''', values=enrollments_values, as_dict=1)

    divisions = [e.student_group for e in enrollments]
    classes = [e.program for e in enrollments]

    notices_values = {
        'student_names': student_names,
        'classes': classes,
        'divisions': divisions,
        "limit": limit
    }

    notices = frappe.db.sql('''
        select *
        from `tabSchool Notice` notice
        where (student in %(student_names)s and is_generic_notice = 0)
            or (
                is_generic_notice = 1 and (
                (notice.division in %(divisions)s)
                or (notice.division is null and notice.class in %(classes)s)
            )
        )
        order by creation desc
        limit %(limit)s;
    ''', values=notices_values, as_dict=1)

    to_skip = (page - 1) * limit
    skipped = 0
    final_notices = []
    for notice in notices:
        if notice.is_generic_notice:
            for student in students:
                for enrollment in enrollments:
                    if student.name == enrollment.student and (
                        notice.division == enrollment.student_group or
                        (not notice.division and notice.get('class') == enrollment.program)
                    ):
                        if to_skip and skipped < to_skip:
                            skipped += 1
                            continue
                        final_notices.append({
                            **notice,
                            'notice': render_jinja(notice.notice, student),
                            'subject': render_jinja(notice.subject, student),
                            "student_first_name": student_dict[student.name].first_name,
                            "student": student.name
                        })
        else:
            if to_skip and skipped < to_skip:
                skipped += 1
                continue

            final_notices.append({
                **notice,
                "student_first_name": student_dict[notice.student].first_name
            })

        if limit and 0 < limit <= len(final_notices):
            break

    return {
        "data": final_notices,
        "total": len(final_notices),
    }


@frappe.whitelist()
def get_notice_by_id(id, student=None):
    school_notice_doc = frappe.get_doc("School Notice", id)
    school_notice = school_notice_doc.as_dict()
    if student and school_notice.is_generic_notice:
        student_doc = frappe.get_doc("Student", student)
        student_data = student_doc.as_dict()
        school_notice = {
            **school_notice,
            'notice': render_jinja(school_notice_doc.notice, student_data),
            'subject': render_jinja(school_notice_doc.subject, student_data),
            "student_first_name": student_doc.first_name,
            "student": student_doc.name
        }
    elif school_notice_doc.student:
        school_notice["student_first_name"] = frappe.db.get_value("Student", school_notice.student, "first_name")

    return {
        "data": school_notice,
    }
