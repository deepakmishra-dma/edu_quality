# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe


def get_columns():

    columns = [
        # {
        #     "fieldname": "period",
        #     "label": "Period No.",
        #     "fieldtype": "Data",
        #     "width": 75,
        # },
        {
            "fieldname": "subject",
            "label": "Subject",
            "fieldtype": "Link",
            "options": "Course",
            "width": 150,
        },
        {
            "fieldname": "textbook",
            "label": "Textbook",
            "fieldtype": "Link",
            "options": "Textbook",
            "width": 150,
        },
        {
            "fieldname": "chapter",
            "label": "Chapter",
            "fieldtype": "Link",
            "options": "Topic",
            "width": 150,
        },
        {
            "fieldname": "real_date",
            "label": "Real Date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "fieldname": "item",
            "label": "Item",
            "fieldtype": "Link",
            "options": "Item",
            "width": 150,
        },
        {
            "fieldname": "item_group",
            "label": "Item Group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 150,
        },
    ]
    return columns


def get_data(filters):
    print(filters)
    division = filters.get("division")
    unit = filters.get("unit")

    cmap_assig_table = frappe.qb.DocType("CMAP Assignment")
    cmap_table = frappe.qb.DocType("CMAP")

    item_detail_table = frappe.qb.DocType("Item Detail")
    frappe.errprint(division)
    frappe.errprint(unit)
    all_assigned_cmap = (
        frappe.qb.from_(cmap_assig_table)
        .inner_join(cmap_table)
        .on(cmap_assig_table.parent == cmap_table.name)
        .where((cmap_assig_table.division == division) & (cmap_table.unit == unit))
        .select(
            cmap_table.name.as_("cmap_name"),
            cmap_assig_table.division,
            cmap_table.subject,
            cmap_table.reserved_for_portion_circular,
            cmap_assig_table.real_date,
        )
    )
    frappe.errprint("test")
    frappe.errprint(all_assigned_cmap.run(as_dict=True))
    find_filtered_cmap = (
        frappe.qb.from_(all_assigned_cmap)
        .left_join(item_detail_table)
        .on(item_detail_table.parent == all_assigned_cmap.cmap_name)
        .where(
            (all_assigned_cmap.reserved_for_portion_circular == 1)
            | (item_detail_table.item_group == "For Portion Circular")
        )
        .orderby(all_assigned_cmap.real_date, frappe.qb.asc)
    ).select("*")

    return find_filtered_cmap.run(as_dict=True)


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data
