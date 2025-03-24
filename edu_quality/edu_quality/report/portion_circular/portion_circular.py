# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

from frappe.query_builder.functions import Count, GROUP_CONCAT, Concat
from frappe.query_builder import Order, Case
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
    division = filters.get("division")
    unit = filters.get("unit")

    cmap_assig_table = frappe.qb.DocType("CMAP Assignment")
    cmap_table = frappe.qb.DocType("CMAP")
    item_table = frappe.qb.DocType("Item")
    item_detail_table = frappe.qb.DocType("Item Detail")

    all_assigned_cmap = (
        frappe.qb.from_(cmap_table)
        .inner_join(cmap_assig_table)
        .on(cmap_assig_table.parent == cmap_table.name)
        .where((cmap_assig_table["division"] == division) & (cmap_table.unit == unit))
        .select(
            cmap_table.name.as_("cmap_name"),
            cmap_table.subject,
            cmap_table.reserved_for_portion_circular,
            cmap_assig_table.real_date,
        )
    )
    item_groups = frappe.db.get_all(
        "Item Group", filters={"custom_hide_in_walsh": 0}, fields=["name"]
    )
    item_group_names = [i.get("name") for i in item_groups]
    find_filtered_cmap = (
        frappe.qb.from_(all_assigned_cmap)
        .left_join(item_detail_table)
        .on(item_detail_table.parent == all_assigned_cmap.cmap_name)
        .inner_join(item_table)
        .on(item_detail_table.item == item_table.name)
        .where(
            (item_detail_table.item_group.isin(item_group_names or [None]))
            & (item_table.custom_hide_in_walsh == 0)
        )
        .groupby(
            all_assigned_cmap.subject,
            item_detail_table.chapter,
            item_detail_table.item_group,
        )
        .orderby(all_assigned_cmap.subject, Order.asc)
    ).select(
        all_assigned_cmap.cmap_name,
        all_assigned_cmap.subject,
        all_assigned_cmap.reserved_for_portion_circular,
        item_detail_table.chapter,
        item_detail_table.textbook,
        item_detail_table.item_group,
        Count(item_detail_table.item).distinct().as_("count"),
        GROUP_CONCAT(item_detail_table.item).distinct().as_("item_names"),
        GROUP_CONCAT(
            Case()
            .when(
                (all_assigned_cmap.reserved_for_portion_circular == 0)
                & (all_assigned_cmap.real_date.isnull()),
                item_detail_table.item,
            )
            .else_(item_table.custom_product_url)
        )
        .distinct()
        .as_("item_urls"),
    )

    return find_filtered_cmap.run(as_dict=True)


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data
