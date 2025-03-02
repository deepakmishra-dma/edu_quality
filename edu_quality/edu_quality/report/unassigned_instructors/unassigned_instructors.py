# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe


def get_columns():
    columns = [
        {
            "fieldname": "teacher",
            "label": "Unassigned Teacher",
            "fieldtype": "Link",
            "options": "Instructor",
            "width": 300,
        },
    ]
    return columns


def get_data(filters):
    cmap_assign_table = frappe.qb.DocType("CMAP Assignment")
    cmap_table = frappe.qb.DocType("CMAP")
    instructor_table = frappe.qb.DocType("Instructor")
    academic_year = filters.get("academic_year")
    school = filters.get("school")

    if not academic_year:
        return []

    query = (
        frappe.qb.from_(cmap_table)
        .inner_join(cmap_assign_table)
        .on(cmap_assign_table.parent == cmap_table.name)
        .where(
            (cmap_table.academic_year == academic_year)
            & (cmap_assign_table.school == school)
        )
        .select(cmap_assign_table.teacher.as_("teacher"))
    )
    frappe.errprint(query.run(as_dict=True))
    left_query = (
        frappe.qb.from_(instructor_table)
        .left_join(query)
        .on(instructor_table.name == query.teacher)
        .where(instructor_table.custom_school == school)
        .select(instructor_table.name, query.teacher)
    )
    final_query = (
        frappe.qb.from_(left_query)
        .where((left_query.teacher.isnull()))
        .select(left_query.name.as_("teacher"))
    )
    frappe.errprint(final_query)
    return final_query.run(as_dict=True)


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data
