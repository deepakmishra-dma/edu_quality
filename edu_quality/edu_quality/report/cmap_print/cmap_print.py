# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import Count, Max
from frappe.utils import parse_json, today, getdate
from edu_quality.edu_quality.server_scripts.utils import calculate_strength_previous


def generate_school_fields(program=None):
    if program:
        programs = frappe.get_list(
            "Program",
            filters={"program_name": program},
            fields=["school", "name", "school", "program_name"],
            ignore_permissions=True,
        )
        schools_set = set([i.get("school") for i in programs])
        frappe.errprint(programs)
        schools = [{"name": i} for i in schools_set]
        frappe.errprint(schools_set)
        frappe.errprint(schools)
    else:
        schools = frappe.get_list("School")
    school_array = []
    for i in schools:
        school_array.append(
            {
                "fieldname": f"qty_for_{i.get('name')}",
                "label": f"{i.get('name')}",
                "fieldtype": "Data",
                "width": 200,
            },
        ),
    return school_array


def generate_extra_school_qty(program):
    if program:
        programs = frappe.get_list(
            "Program",
            filters={"program_name": program},
            fields=["school", "name", "school", "program_name"],
            ignore_permissions=True,
        )
        schools_set = set([i.get("school") for i in programs])
        frappe.errprint(programs)
        schools = [{"name": i} for i in schools_set]
        frappe.errprint(schools_set)
        frappe.errprint(schools)
    else:
        schools = frappe.get_list("School")
    school_array = []
    for i in schools:
        school_array.append(
            {
                "fieldname": f"extra_qty_for_{i.get('name')}",
                "label": f"Extra Qty {i.get('name')}",
                "fieldtype": "Data",
                "width": 250,
            },
        )
    return school_array


@frappe.whitelist()
def get_school_fields_sum(row):
    school_fields = generate_school_fields()
    school_fields_to_sum = [school.get("fieldname") for school in school_fields]
    frappe.errprint(row)
    return sum(
        [
            row.get(field, 0) + row.get(f"extra_{field}", 0)
            for field in school_fields_to_sum
        ]
    )


def get_columns(filters):
    school_fields = generate_school_fields(filters.get("class"))
    extra_fields = generate_extra_school_qty(filters.get("class"))
    columns = [
        # {
        #     "fieldname": "period",
        #     "label": "Period No.",
        #     "fieldtype": "Data",
        #     "width": 75,
        # },
        {
            "fieldname": "product_code",
            "label": "Product Code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 75,
        },
        {
            "fieldname": "planned_Date",
            "label": "Planned Date",
            "fieldtype": "Date",
            "hidden": 1,
        },
        {
            "fieldname": "chapter",
            "label": "Chapter Name",
            "fieldtype": "Link",
            "options": "Topic",
            "width": 160,
        },
        # {
        #     "fieldname": "added_in_cmap",
        #     "label": "Added in CMAP",
        #     "fieldtype": "Data",
        #     "width": 50,
        # },
        *school_fields,
        *extra_fields,
        # {
        #     "fieldname": "extra_qty_per_school",
        #     "label": "Extra Quantity per school",
        #     "fieldtype": "Data",
        #     "width": 175,
        # },
        {
            "fieldname": "total_quantity",
            "label": "Total Quantity",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "fieldname": "sent_to_print",
            "label": "Sent to Print On",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "fieldname": "sent_by",
            "label": "Sent By",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "fieldname": "received_from_printer_on",
            "label": "Received from printer on",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "fieldname": "received_by",
            "label": "Received By",
            "fieldtype": "Data",
            "width": 175,
        },
    ]
    return columns


def transform_data(
    program_enrollments, CMAPS, class_filter, products_max_data, products_rec_data
):
    # converting the dict array received to a hashmap
    converted_dict = {item["program"]: item["count"] for item in program_enrollments}
    max_hash = {}
    for i in products_max_data:
        item_code = i.get("item_code")
        max_hash[item_code] = i
    products_rec_hash = {}
    for i in products_rec_data:
        item_code = i.get("item_code")
        products_rec_hash[item_code] = i

    data = []
    school_fields = generate_school_fields(class_filter)
    for i in CMAPS:
        for school in school_fields:
            if i.get("product_code") in max_hash:
                i["sent_to_print"] = max_hash[i.get("product_code")].get("transaction")
                i["sent_by"] = max_hash[i.get("product_code")].get("sent_by")
            if i.get("product_code") in products_rec_hash:
                i["received_from_printer_on"] = products_rec_hash[
                    i.get("product_code")
                ].get("received_date")
                i["received_by"] = products_rec_hash[i.get("product_code")].get(
                    "received_by"
                )

            i[school.get("fieldname")] = (
                converted_dict.get(f'{i.get("class")}-{school.get("label")}', 0) or 0
            )

            i[f"extra_{school.get('fieldname')}"] = frappe.db.get_value(
                "School", school.get("label"), "custom_extra_print_qty"
            )

        i["total_quantity"] = get_school_fields_sum(i)

        data.append(i)
    return data


def check_if_academic_year_is_next(academic_year):
    try:
        academic_year = frappe.get_doc(
            "Academic Year", filters={"name": academic_year}, fields=["year_start_date"]
        )
        if getdate(academic_year.get("year_start_date"), "") > today():
            return True
        return False
    except Exception as e:
        return False


def get_data_from_queries(filters=None):
    # gets list of cmaps

    item_detail = frappe.qb.DocType("Item Detail")
    cmap = frappe.qb.DocType("CMAP")
    item = frappe.qb.DocType("Item")
    purchase_ord_table = frappe.qb.DocType("Purchase Order")
    purchase_ord_item_table = frappe.qb.DocType("Purchase Order Item")
    purchase_rec_table = frappe.qb.DocType("Purchase Receipt")
    purchase_rec_item_table = frappe.qb.DocType("Purchase Receipt Item")

    item_group = frappe.qb.DocType("Item Group")
    class_filter = filters.get("class")
    subject_filter = filters.get("subject")
    unit_filter = filters.get("unit")

    cmap_query = (
        frappe.qb.from_(cmap)
        .inner_join(item_detail)
        .on(cmap.name == item_detail.parent)
        .inner_join(item)
        .on(item_detail.item == item.name)
        .inner_join(item_group)
        .on(item.item_group == item_group.name)
        .where(
            (cmap.academic_year == filters.get("academic_year"))
            & (cmap["class"] == class_filter)
            & (cmap.subject.isin(subject_filter if len(subject_filter) else [None]))
            & (cmap.unit.isin(unit_filter if len(unit_filter) else [None]))
            & (cmap.reserved_for_portion_circular == 0)
            & (
                (
                    cmap.plan_date[
                        filters.get("start_plan_date") : filters.get("end_plan_date")
                    ]
                )
                | (cmap.plan_date.isnull())
            )
            & (item.custom_is_cmap == 1)
            & (item.custom_print_ready == 1)
            & (item_group.custom_printable == 1)
        )
        .groupby(item_detail.item)
        .select(
            item.custom_chapter.as_("chapter"),
            cmap.name,
            cmap["class"],
            cmap.plan_date,
            item_detail.item.as_("product_code"),
        )
    )
    cmap_data = cmap_query.run(as_dict=True)
    frappe.errprint(str(cmap_query))

    student = frappe.qb.DocType("Student")
    program_enrollment = frappe.qb.DocType("Program Enrollment")
    count_all = Count("*").as_("count")

    # gets count of students on on basis of program/class not class type
    # TODO: Implement new academic year students logic
    academic_year_doc = frappe.get_doc(
        "Academic Year",
        filters.get("academic_year"),
        fields=["custom_current_academic_year", "custom_next_academic_year"],
    )

    current_academic_year = frappe.get_value(
        "Academic Year", {"custom_current_academic_year": 1}, "name"
    )
    qty_needed_for_schools_query = ""

    qty_needed_for_schools_query = (
        frappe.qb.from_(student)
        .inner_join(program_enrollment)
        .on(student.name == program_enrollment.student)
        .where(
            (program_enrollment.academic_year == filters.get("academic_year"))
            & (program_enrollment.program.like(f'{filters.get("class")}-%'))
            & (program_enrollment.docstatus == 1)
        )
        .groupby(program_enrollment.program)
        .select(count_all, program_enrollment.program)
    )

    products = [i.get("product_code") for i in cmap_data]
    products_max_query = (
        frappe.qb.from_(purchase_ord_item_table)
        .inner_join(purchase_ord_table)
        .on(purchase_ord_item_table.parent == purchase_ord_table.name)
        .where(
            (purchase_ord_item_table.item_code.isin(products or [None]))
            & (purchase_ord_table.custom_class == filters.get("class"))
        )
        .groupby(purchase_ord_item_table.item_code)
        .select(
            purchase_ord_item_table.item_code,
            Max(purchase_ord_table.transaction_date).as_("transaction"),
            purchase_ord_table.custom_sent_by.as_("sent_by"),
            purchase_ord_table.name,
        )
    )

    # products_query = frappe.qb.from_(purchase_ord_item_table).inner_join(group_products_query)
    products_max_data = products_max_query.run(as_dict=True)
    purchase_orders = [i.get("name") for i in products_max_data]

    products_rec_query = (
        frappe.qb.from_(purchase_rec_item_table)
        .inner_join(purchase_rec_table)
        .on(purchase_rec_table.name == purchase_rec_item_table.parent)
        .where(purchase_rec_item_table.purchase_order.isin(purchase_orders or [None]))
        .groupby(purchase_rec_item_table.purchase_order)
        .select(
            purchase_rec_item_table.item_code,
            Max(purchase_rec_table.custom_receiving_date).as_("received_date"),
            Max(purchase_rec_table.custom_received_by).as_("received_by"),
        )
    )

    products_rec_data = products_rec_query.run(as_dict=True)
    qty_needed_for_schools = qty_needed_for_schools_query.run(as_dict=True)

    frappe.errprint(qty_needed_for_schools)
    return transform_data(
        qty_needed_for_schools,
        cmap_data,
        class_filter,
        products_max_data,
        products_rec_data,
    )


def execute(filters=None):
    frappe.errprint(filters)
    columns = get_columns(filters)

    data = get_data_from_queries(filters)
    return columns, data


@frappe.whitelist()
def create_purchase_order(rows, academic_year=None, class_name=None):
    if isinstance(rows, str):
        rows = parse_json(rows)

    school_fields = generate_school_fields()
    purchase_order = frappe.get_doc(
        {
            "doctype": "Purchase Order",
            "purpose": "Purchase",
            "items": [],
            "supplier": "Printer",
            "custom_is_cmap_print": 1,
            "custom_class": class_name,
            "custom_academic_year": academic_year,
        }
    )

    for row in rows:
        for school in school_fields:
            append_items(purchase_order, row, school)

    if len(rows):
        purchase_order.insert()
    return purchase_order


def append_items(purchase_order, row, school_field):
    school_doc = frappe.get_doc("School", school_field.get("label"))

    if int(row.get(school_field.get("fieldname", 0), 0)) == 0:
        return

    purchase_order.append(
        "items",
        {
            "item_code": row.get("product_code"),
            "qty": int(row.get(school_field.get("fieldname", 0), 0))
            + int(row.get("extra_" + school_field.get("fieldname", 0), 0)),
            "schedule_date": frappe.utils.nowdate(),
            "warehouse": school_doc.get("warehouse"),
            "uom": "Nos",
            "school": school_doc.get("name", None),
        },
    )
