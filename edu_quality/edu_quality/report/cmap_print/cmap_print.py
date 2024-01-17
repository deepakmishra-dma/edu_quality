# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import Count
from frappe.utils import parse_json

# def generate_school_fields():
#     schools = frappe.get_list("School")
#     school_array = []
#     for i in schools:
#         school_array.append(
#             {
#                 "fieldname": f"qty_for_{i}",
#                 "label": "Quantity for {i}",
#                 "fieldtype": "Data",
#                 "width": 100,
#             }
#         ),
#     return school_array


def get_columns():
    columns = [
        {
            "fieldname": "period",
            "label": "Period No.",
            "fieldtype": "Data",
            "width": 75,
        },
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
        {
            "fieldname": "qty_for_shivane",
            "label": "Walnut School Shivane",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "fieldname": "qty_for_Fursungi",
            "label": "Walnut School Fursungi",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "fieldname": "qty_for_Wakad",
            "label": "Walnut School Wakad",
            "fieldtype": "Data",
            "width": 175,
        },
        {
            "fieldname": "extra_qty_per_school",
            "label": "Extra Quantity per school",
            "fieldtype": "Data",
            "width": 175,
        },
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


def transform_data(program_enrollments, CMAPS):
    # converting the dict array received to a hashmap
    converted_dict = {item["program"]: item["count"] for item in program_enrollments}
    data = []
    for i in CMAPS:
        i["qty_for_shivane"] = (
            converted_dict.get(f'{i.get("class")}-Walnut School at Shivane', 0) or 0
        )

        i["qty_for_wakad"] = (
            converted_dict.get(f'{i.get("class")}-Walnut School at Wakad', 0) or 0
        )

        i["qty_for_fursungi"] = (
            converted_dict.get(f'{i.get("class")}-Walnut School at Fursungi', 0) or 0
        )
        i["extra_qty_per_school"] = 30
        i["total_quantity"] = (
            i["qty_for_shivane"]
            + i["qty_for_wakad"]
            + i["qty_for_fursungi"]
            + i["extra_qty_per_school"]
        )

        data.append(i)
    return data


def get_data_from_queries(filters=None):
    # gets list of cmaps

    item_detail = frappe.qb.DocType("Item Detail")
    cmap = frappe.qb.DocType("CMAP")
    item = frappe.qb.DocType("Item")
    class_filter = filters.get("class")
    subject_filter = filters.get("subject")
    unit_filter = filters.get("unit")
    cmap_query = (
        frappe.qb.from_(cmap)
        .inner_join(item_detail)
        .on(cmap.name == item_detail.parent)
        .inner_join(item)
        .on(item_detail.item == item.name)
        .where(
            (cmap.academic_year == filters.get("academic_year"))
            & (cmap["class"].isin(class_filter if len(class_filter) else [None]))
            & (cmap.subject.isin(subject_filter if len(subject_filter) else [None]))
            & (cmap.unit.isin(unit_filter if len(unit_filter) else [None]))
            & (
                cmap.plan_date[
                    filters.get("start_plan_date") : filters.get("end_plan_date")
                ]
            )
            & (item.custom_is_cmap == 1)
            & (item.custom_print_ready == 1)
        )
        .select(
            cmap.period,
            cmap.chapter,
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
    qty_needed_for_schools_query = (
        frappe.qb.from_(student)
        .inner_join(program_enrollment)
        .on(student.name == program_enrollment.student)
        .where(
            (student.student_state.isin(["Current", "Defaulter"]))
            & (program_enrollment.academic_year == filters.get("academic_year"))
        )
        .groupby(program_enrollment.program)
        .select(count_all, program_enrollment.program)
    )

    frappe.errprint(str(qty_needed_for_schools_query))
    qty_needed_for_schools = qty_needed_for_schools_query.run(as_dict=True)

    frappe.errprint(qty_needed_for_schools)
    return transform_data(qty_needed_for_schools, cmap_data)


def execute(filters=None):
    frappe.errprint(filters)
    columns = get_columns()

    data = get_data_from_queries(filters)
    return columns, data


@frappe.whitelist()
def create_material_request(rows):
    if isinstance(rows, str):
        rows = parse_json(rows)
    material_request = frappe.get_doc(
        {"doctype": "Material Request", "purpose": "Purchase", "items": []}
    )
    for row in rows:
        material_request.append(
            "items",
            {
                "item_code": row.get("product_code"),
                "qty": row.get("total_quantity"),
                "schedule_date": frappe.utils.nowdate(),
                "uom": "Nos",
            },
        )
    if len(rows):
        material_request.insert()
