import frappe
from edu_quality.edu_quality.report.portion_circular.portion_circular import get_data
from datetime import datetime
from edu_quality.public.py.walsh.login import logout


@frappe.whitelist()
def get_students():
    user = frappe.session.user

    cache_key = f"walsh:guardian_students_{user}"
    students_cache = frappe.cache().get_value(cache_key)

    if students_cache:
        return students_cache

    guardian = frappe.get_cached_doc("Guardian", {"user": user})
    all_student_data = frappe.get_all(
        "Student", filters={"guardian": guardian.name}, fields=["*"]
    )

    student_disabled = all(student.get("enabled") == 0 for student in all_student_data)
    # if all of student disabled log out the parent
    if student_disabled:
        logout()

        frappe.throw(("Not permitted"), frappe.PermissionError)
        return []

    students = [student for student in all_student_data if student.get("enabled")]

    # Cache the results for 10 minutes
    frappe.cache().set_value(cache_key, students, expires_in_sec=600)
    return students


@frappe.whitelist(allow_guest=True)
def get_student_class_details(student):
    current_yr = frappe.db.get_value(
        "Academic Year", {"custom_current_academic_year": 1}
    )
    program_enrollments = frappe.get_all(
        "Program Enrollment",
        filters={"student": student, "academic_year": current_yr, "docstatus": 1},
        fields=["program", "student_group"],
    )
    if not len(program_enrollments):
        return {}

    program = program_enrollments[0]["program"]
    program_data = frappe.get_cached_doc("Program", program)
    class_type = frappe.get_cached_doc("Class Type", program_data.program_name)
    division = frappe.get_cached_doc(
        "Student Group", program_enrollments[0]["student_group"]
    )

    return {"division": division, "program": program_data, "class": class_type}


@frappe.whitelist()
def get_all_cmap_in_range(date, division):

    if not date or not division:
        return []

    begin_date, end_date = list(map(lambda x: x.strip(), date.split(",")))

    values = {"begin_date": begin_date, "division": division, "end_date": end_date}

    cmaps = frappe.db.sql(
        """
        select *,
         (select real_date from `tabCMAP Assignment` ta where division = %(division)s and real_date between %(begin_date)s and %(end_date)s and
          ta.parent = c.name limit 1)          as real_date         from `tabCMAP` as c
        where name in (
            select parent from `tabCMAP Assignment` ta2 where real_date between %(begin_date)s and %(end_date)s and
            division = %(division)s and ta2.parent = c.name
        ) and reserved_for_portion_circular = 0
        order by real_date desc
        """,
        as_dict=1,
        values=values,
    )

    modified_cmaps = generate_cmap_data_from_query(cmaps)
    result_hash = {}
    for cmap in modified_cmaps:
        subject = cmap.get("subject")
        unit = cmap.get("unit")
        if subject not in result_hash:
            result_hash[subject] = {unit: [cmap]}
        elif unit not in result_hash[subject]:
            result_hash[subject][unit] = [cmap]
        elif unit in result_hash[subject]:
            result_hash[subject][unit].append(cmap)
    return result_hash


def generate_cmap_data_from_query(cmaps):
    cmap_names = [cmap.name for cmap in cmaps]
    all_products = frappe.get_all(
        "Item Detail", filters={"parent": ["in", cmap_names]}, fields=["*"]
    )
    valid_item_groups = frappe.get_all(
        "Item Group", filters={"custom_hide_in_walsh": 0}, fields=["*"]
    )
    item_group_names = [p.name for p in valid_item_groups]
    item_names = [p.item for p in all_products]
    all_items = frappe.get_all(
        "Item",
        fields=["*"],
        filters={
            "name": ["in", item_names],
            "item_group": ["in", item_group_names],
            "custom_hide_in_walsh": 0,
        },
    )
    broadcast_names = [
        product.broadcast for product in all_products if product.broadcast
    ]
    homework_names = [
        product.home_work for product in all_products if product.home_work
    ]
    parentnote_names = [
        product.parent_note for product in all_products if product.parent_note
    ]
    # cmap_materials = frappe.get_all("Item CMAP Material", fields=["*"], filters={"name": ["in", cmap_material_names]})

    for product in all_products:
        for item in all_items:
            if item.name == product.item:
                product["hide_in_walsh"] = (
                    bool(item.custom_hide_in_walsh)
                    or item.item_group not in item_group_names
                )
                product["item_data"] = item
        for broadcast in broadcast_names:
            if broadcast == product.broadcast:
                product["broadcast_description"] = broadcast
        for homework in homework_names:
            if homework == product.home_work:
                product["homework_description"] = homework
        for parentnote in parentnote_names:
            if parentnote == product.parent_note:
                product["parentnote_description"] = parentnote

    for cmap in cmaps:
        cmap.products = []
        for product in all_products:
            if product.parent == cmap.name:
                cmap.products.append(product)

    return cmaps


@frappe.whitelist()
def get_all_cmaps(subject, unit, division):
    values = {"subject": subject, "unit": unit, "division": division}
    cmaps = frappe.db.sql(
        """
        select *,
         (select real_date from `tabCMAP Assignment` ta where division = %(division)s and real_date <= CURDATE() and
          ta.parent = c.name limit 1)          as real_date         from `tabCMAP` as c
        where subject = %(subject)s
        and unit = %(unit)s
        and name in (
            select parent from `tabCMAP Assignment` ta2 where real_date <= CURDATE() and
            division = %(division)s and ta2.parent = c.name
        ) and reserved_for_portion_circular = 0
        order by real_date desc
        """,
        as_dict=1,
        values=values,
    )

    return generate_cmap_data_from_query(cmaps)


@frappe.whitelist(allow_guest=True)
def get_portion_circulars(unit, division):

    payload = {"unit": unit, "division": division}
    data = get_data(payload)
    subject_hash = {}
    for i in data:
        subject = i["subject"]
        textbook = i["textbook"]
        chapter = i["chapter"]
        item_names = i["item_names"].split(",") or []
        item_urls = i["item_urls"].split(",") or []
        products = i["products"]

        if subject not in subject_hash:
            subject_hash[subject] = {textbook: {chapter: [i]}}

        elif textbook not in subject_hash[subject]:
            subject_hash[subject][textbook] = {chapter: [i]}

        elif chapter not in subject_hash[subject][textbook]:

            subject_hash[subject][textbook][chapter] = [i]

        else:

            subject_hash[subject][textbook][chapter].append(i)

    return subject_hash
