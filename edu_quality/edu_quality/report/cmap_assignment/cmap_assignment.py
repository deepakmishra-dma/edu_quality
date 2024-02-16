# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe


def get_columns():
    columns = [
        {
            "fieldname": "period",
            "label": "Period No.",
            "fieldtype": "Data",
            "width": 75,
        },
        {
            "fieldname": "chapter_name",
            "label": "Chapter Name",
            "fieldtype": "Link",
            "options": "Topic",
            "width": 75,
        },
        {
            "fieldname": "division",
            "label": "Division",
            "fieldtype": "Link",
            "options": "Student Group",
        },
        {
            "fieldname": "teacher",
            "label": "Teacher",
            "fieldtype": "Link",
            "options": "Instructor",
            "width": 160,
        },
        {
            "fieldname": "plan_date",
            "label": "Plan Date",
            "fieldtype": "Date",
            "width": 160,
        },
    ]
    return columns


def get_data_from_queries(filters=None):
    cmap = frappe.qb.DocType("CMAP")
    cmap_assignment = frappe.qb.DocType("CMAP Assignment")
    class_filter = filters.get("class")
    subject_filter = filters.get("subject")
    school_filter = filters.get("school")
    unit_filter = filters.get("unit")
    academic_year = filters.get("academic_year")
    cmap_query = (
        frappe.qb.from_(cmap)
        .inner_join(cmap_assignment)
        .on(cmap.name == cmap_assignment.parent)
        .where(
            (cmap.academic_year == academic_year)
            & (cmap["class"] == class_filter)
            & (cmap.subject == subject_filter)
            & (cmap.unit == unit_filter)
            & (cmap_assignment.school == school_filter)
        )
        .select(
            cmap.period.as_("period"),
            cmap.chapter.as_("chapter_name"),
            cmap_assignment.division.as_("division"),
            cmap_assignment.teacher.as_("teacher"),
            cmap.plan_date.as_("plan_date"),
        )
    )
    frappe.errprint(cmap_query)
    cmap_data = cmap_query.run(as_dict=True)
    frappe.errprint(cmap_data)
    return cmap_data


def execute(filters=None):
    columns, data = get_columns(), get_data_from_queries(filters)
    return columns, data
