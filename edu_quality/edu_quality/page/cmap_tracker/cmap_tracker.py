import frappe
import json


# edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.get_cmap
@frappe.whitelist()
def get_cmap(**filters):
    cmap_table = frappe.qb.DocType("CMAP")
    cmap_assign_table = frappe.qb.DocType("CMAP Assignment")
    products_table = frappe.qb.DocType("Item Detail")
    item_table = frappe.qb.DocType("Item")

    filtered_cmap_query = (
        frappe.qb.from_(cmap_table)
        .where(
            (cmap_table.academic_year == filters.get("academic_year"))
            & (cmap_table.subject == filters.get("subject"))
            & (cmap_table.unit == filters.get("unit"))
            & (cmap_table["class"] == filters.get("class"))
        )
        .select(
            cmap_table.name,
            cmap_table.academic_year,
            cmap_table.period,
            cmap_table.plan_date,
        )
    )

    filtered_cmap_product_query = (
        frappe.qb.from_(filtered_cmap_query)
        .inner_join(products_table)
        .on(filtered_cmap_query.name == products_table.parent)
        .select(
            filtered_cmap_query.name,
            products_table.broadcast,
            products_table.item.as_("item_code"),
            products_table.parent_note,
            products_table.home_work,
            products_table.textbook,
            products_table.chapter,
        )
    )

    products_data = filtered_cmap_product_query.run(as_dict=True)

    filtered_assigned_query = (
        frappe.qb.from_(filtered_cmap_query)
        .inner_join(cmap_assign_table)
        .on(filtered_cmap_query.name == cmap_assign_table.parent)
        .select(
            filtered_cmap_query.star,
            cmap_assign_table.teacher,
            cmap_assign_table.school,
            cmap_assign_table.division,
            cmap_assign_table.real_date,
        )
    )

    return cocatenate_cmap(filtered_assigned_query.run(as_dict=True), products_data)


def cocatenate_cmap(data, products_data):
    product_hash = {}
    for product in products_data:
        cmap_name = product.get("name")

        if cmap_name not in product_hash:
            product_hash[cmap_name] = [product]
        else:
            product_hash[cmap_name].append(product)
    frappe.errprint(product_hash)
    for cmap in data:
        cmap_name = cmap.get("name")
        if cmap_name in product_hash:
            cmap["products"] = [i.get("item_code") for i in product_hash[cmap_name]]

            cmap["chapter_name"] = ",".join(
                set([i.get("chapter") for i in product_hash[cmap_name]])
            )
    return data


# edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.update
@frappe.whitelist()
def update(filters, cmap_data):
    filters = json.loads(filters) if isinstance(filters, str) else filters
    cmap_data = json.loads(cmap_data) if isinstance(cmap_data, str) else cmap_data

    for assignments in cmap_data:
        cmap = frappe.get_doc("CMAP", assignments.get("name"))

        for item in cmap.table_vwbr:
            if (
                item.school == filters.get("school")
                and item.division == assignments.get("division")
                and item.teacher == assignments.get("teacher")
            ):
                # Update existing teacher
                item.real_date = assignments.get("real_date")
        cmap.save()

    return
