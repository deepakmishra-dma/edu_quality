# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe


def get_columns():
    columns = [
        {
            "fieldname": "division",
            "label": "Unassigned Division",
            "fieldtype": "Link",
            "options": "Student Group",
            "width": 300,
        },
        {
            "fieldname": "program",
            "label": "Program",
            "fieldtype": "Link",
            "options": "Program",
            "width": 200,
        },
        {
            "fieldname": "custom_school",
            "label": "School",
            "fieldtype": "Link",
            "options": "School",
            "width": 200,
        },
        {
            "fieldname": "subject",
            "label": "Subject",
            "fieldtype": "Link",
            "options": "Course",
            "width": 200,
        },
        {
            "fieldname": "period",
            "label": "Period",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "unit",
            "label": "Unit",
            "fieldtype": "Data",
            "width": 200,
        },
    ]
    return columns


def get_data(filters):
    cmap_assign_table = frappe.qb.DocType("CMAP Assignment")
    cmap_table = frappe.qb.DocType("CMAP")
    div_table = frappe.qb.DocType("Student Group")
    academic_year = filters.get("academic_year")
    school = filters.get("school")

    if not academic_year:
        return []

    query = (
        frappe.qb.from_(div_table)
        .where(
            (div_table.custom_school == school)
            & (div_table.academic_year == academic_year)
        )
        .select("name", "program", "custom_school")
    )
    cmap_query = (
        frappe.qb.from_(cmap_table)
        .inner_join(cmap_assign_table)
        .on(cmap_assign_table.parent == cmap_table.name)
        .where(
            (cmap_table.academic_year == academic_year)
            & (cmap_assign_table.school == school)
        )
        .select(
            cmap_assign_table.division,
            cmap_table.subject,
            cmap_table.period,
            cmap_table.unit,
        )
    )

    final_query = (
        frappe.qb.from_(query)
        .left_join(cmap_query)
        .on(query.name == cmap_query.division)
        .where(cmap_query.division.isnull())
    ).select(
        query.name.as_("division"),
        query.program,
        query.custom_school,
        cmap_query.subject,
        cmap_query.period,
        cmap_query.unit,
    )

    frappe.errprint(final_query)
    return final_query.run(as_dict=True)


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data
