# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

from frappe.query_builder.functions import Count, GROUP_CONCAT, Concat
from frappe.query_builder import Order, Case
import frappe
from pypika.functions import DistinctOptionFunction
from pypika import Field, MySQLQuery, Order

QUOTE_CHAR = MySQLQuery._builder().QUOTE_CHAR


class GroupConcat(DistinctOptionFunction):
    def __init__(
        self, term: Field, order_field=None, order=Order.asc, sep=",", alias=None
    ):

        super().__init__("GROUP_CONCAT", term, alias=alias)
        self.term_ = term.get_sql(with_alias=False, quote_char=QUOTE_CHAR)
        self.order = order
        self.sep = self.wrap_constant(sep)
        self.order_field = order_field.get_sql(with_alias=False, quote_char=QUOTE_CHAR)

    def get_special_params_sql(self, **kwargs):
        if not self.order_field:
            return ""
        return f"ORDER BY {self.order_field} {self.order.value} SEPARATOR {self.sep}"


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
        {
            "fieldname": "item_names",
            "label": "Item Names",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "item_urls",
            "label": "Item Urls",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "fieldname": "count",
            "label": "Count",
            "fieldtype": "Data",
            "width": 150,
        },
    ]
    return columns


def get_data(filters):
    division = filters.get("division")
    unit = filters.get("unit")
    subject = filters.get("subject")

    cmap_assig_table = frappe.qb.DocType("CMAP Assignment")
    cmap_table = frappe.qb.DocType("CMAP")
    item_table = frappe.qb.DocType("Item")
    item_detail_table = frappe.qb.DocType("Item Detail")

    if subject:
        subjects = frappe.db.get_all("Course", filters={"name": subject})
    else:
        subjects = frappe.db.get_all("Course", filters={"custom_hide_in_portion": 0})

    subject_names = [i.get("name") for i in subjects]
    all_assigned_cmap = (
        frappe.qb.from_(cmap_table)
        .inner_join(cmap_assig_table)
        .on(cmap_assig_table.parent == cmap_table.name)
        .where(
            (cmap_assig_table["division"] == division)
            & (cmap_table.unit == unit)
            & (cmap_table.subject.isin(subject_names or [None]))
        )
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
    # dont add distinct in item urls and item names
    find_filtered_cmap = (
        frappe.qb.from_(all_assigned_cmap)
        .left_join(item_detail_table)
        .on(item_detail_table.parent == all_assigned_cmap.cmap_name)
        .inner_join(item_table)
        .on(item_detail_table.item == item_table.name)
        .where(
            (item_detail_table.item_group.isin(item_group_names or [None]))
            & (item_table.custom_hide_in_walsh == 0)
            & (item_detail_table.hide_in_portion_circular == 0)
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
        GroupConcat(item_detail_table.item, order_field=item_detail_table.item).as_(
            "item_names"
        ),
        GroupConcat(
            Case()
            .when(
                (all_assigned_cmap.reserved_for_portion_circular == 0)
                & (all_assigned_cmap.real_date.isnull()),
                item_detail_table.item,
            )
            .else_(item_table.custom_product_url),
            order_field=item_detail_table.item,
        ).as_("item_urls"),
    )

    result = find_filtered_cmap.run(as_dict=True)

    data = dedupe_result(result)
    item_hash = item_url_hash_from_portion_data(data)

    for i in data:
        products = i["products"]
        for j in range(len(products)):
            product = products[j].get("name")
            url = products[j].get("url")
            if url and item_hash[product] != url:
                products[j]["url"] = item_hash[product]
    return data


def item_url_hash_from_portion_data(data):
    all_item_names = []
    for i in data:
        item_names = i["item_names"].split(",") or []
        all_item_names.extend(item_names)
    item_qb = frappe.qb.DocType("Item")
    query = (
        frappe.qb.from_(item_qb)
        .where((item_qb.name.isin(all_item_names or [None])))
        .select("name", "custom_product_url")
    )

    result = query.run(as_dict=True)
    result_hash = {}
    for item in result:
        name = item.get("name")
        custom_product_url = item.get("custom_product_url")
        if name not in result_hash:
            result_hash[name] = custom_product_url
        else:
            continue
    return result_hash


def dedupe_result(data):
    for datum in data:
        hashmap = {}
        item_names = datum["item_names"].split(",") or []
        item_urls = datum["item_urls"].split(",") or []
        for i in range(len(item_names)):
            if not hashmap.get(item_names[i]):
                if item_names[i] != item_urls[i]:
                    hashmap[item_names[i]] = item_urls[i]
                else:
                    hashmap[item_names[i]] = None
        result_items = [{"name": i, "url": hashmap[i]} for i in hashmap]
        datum["products"] = result_items
    return data


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data
