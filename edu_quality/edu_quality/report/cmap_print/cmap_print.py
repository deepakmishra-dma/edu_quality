# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import Count
from frappe.utils import parse_json, today, getdate
from edu_quality.edu_quality.server_scripts.utils import projected_strength


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
            }
        ),
    return school_array


@frappe.whitelist()
def get_school_fields_sum(row):
    school_fields = generate_school_fields()
    school_fields_to_sum = [school.get("fieldname") for school in school_fields]
    frappe.errprint(row)
    return sum(
        [
            row.get(field, 0) + row.get("extra_qty_per_school", 0)
            for field in school_fields_to_sum
        ]
    )


def get_columns(filters):
    school_fields = generate_school_fields(filters.get("class"))
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
        *school_fields,
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


def transform_data(program_enrollments, CMAPS, class_filter):
    # converting the dict array received to a hashmap
    converted_dict = {item["program"]: item["count"] for item in program_enrollments}
    data = []
    school_fields = generate_school_fields(class_filter)
    for i in CMAPS:
        for school in school_fields:
            i[school.get("fieldname")] = (
                converted_dict.get(f'{i.get("class")}-{school.get("label")}', 0) or 0
            )

        i["extra_qty_per_school"] = 30

        i["total_quantity"] = get_school_fields_sum(i)

        data.append(i)
    return data


def check_if_academic_year_is_next(academic_year):
    try:
        academic_year = frappe.db.get_doc(
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
            & (cmap["class"] == class_filter)
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
    if academic_year_doc.custom_next_academic_year:
        qty_needed_for_schools = []
        schools = frappe.db.get_list("School")
        schools = [school.get("name") for school in schools]

        for school in schools:
            try:
                projected_strength = projected_strength(f"{class_filter}-{school}")
            except:
                projected_strength = 0

            qty_needed_for_schools.append(
                {
                    "count": projected_strength,
                    "program": f"{class_filter}-{school}",
                }
            )

    else:
        qty_needed_for_schools_query = (
            frappe.qb.from_(student)
            .inner_join(program_enrollment)
            .on(student.name == program_enrollment.student)
            .where(
                (student.student_status.isin(["Current student", "Defaulter"]))
                & (program_enrollment.academic_year == filters.get("academic_year"))
                & (program_enrollment.program.like(f'{filters.get("class")}-%'))
            )
            .groupby(program_enrollment.program)
            .select(count_all, program_enrollment.program)
        )
        qty_needed_for_schools = qty_needed_for_schools_query.run(as_dict=True)

    frappe.errprint(qty_needed_for_schools)
    return transform_data(qty_needed_for_schools, cmap_data, class_filter)


def execute(filters=None):
    frappe.errprint(filters)
    columns = get_columns(filters)

    data = get_data_from_queries(filters)
    return columns, data


@frappe.whitelist()
def create_purchase_order(rows):
    if isinstance(rows, str):
        rows = parse_json(rows)

    school_fields = generate_school_fields()
    purchase_order = frappe.get_doc(
        {
            "doctype": "Purchase Order",
            "purpose": "Purchase",
            "items": [],
            "supplier": "Printer",
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

    purchase_order.append(
        "items",
        {
            "item_code": row.get("product_code"),
            "qty": int(row.get(school_field.get("fieldname", 0)))
            + int(row.get("extra_qty_per_school", 0)),
            "schedule_date": frappe.utils.nowdate(),
            "warehouse": school_doc.get("warehouse"),
            "uom": "Nos",
            "custom_period": row.get("period"),
        },
    )
