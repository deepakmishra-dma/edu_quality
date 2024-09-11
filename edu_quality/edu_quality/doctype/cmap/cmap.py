# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import parse_json
import json

# edu_quality.edu_quality.doctype.cmap.cmap


class CMAP(Document):
    def autoname(self, method=None):
        course_short_code = frappe.db.get_value(
            "Course", self.subject, "custom_short_code"
        )
        course_doc = frappe.get_doc("Course", self.subject)
        class_sortcode = frappe.db.get_value(
            "Class Type", self.get("class"), "short_code"
        )
        self.name = f"{self.academic_year}-{course_short_code}{class_sortcode}{self.unit}{self.period}"

    def before_validate(self, method=None):
        frappe.errprint(self.products)
        added_broadcasts = [product.get("broadcast") for product in self.products]
        added_parent_notes = [product.get("parent_note") for product in self.products]
        added_home_works = [product.get("home_work") for product in self.products]
        added_material_required = [
            product.get("material_required") for product in self.products
        ]
        added_class_works = [product.get("class_work") for product in self.products]
        generate_text_from_unique_notes(self, "Broadcast", added_broadcasts)
        generate_text_from_unique_notes(self, "Parent Note", added_parent_notes)
        generate_text_from_unique_notes(self, "Home Work", added_home_works)
        generate_text_from_unique_notes(self, "Class Work", added_class_works)
        generate_text_from_unique_notes(
            self, "Material Required", added_material_required
        )

    def after_insert(self, method=None):
        insert_cmap_assignees(self)


def insert_cmap_assignees(self):
    instructors = frappe.db.get_list(
        "Instructor Log",
        filters=[
            ["academic_year", "=", self.academic_year],
            ["program", "LIKE", f"{self.get('class')}-%"],
            ["course", "=", self.subject],
        ],
        fields=[
            "parent",
            "parent",
            "program",
            "student_group",
            "program",
            "program",
        ],
        ignore_permissions=True,
    )
    frappe.errprint(instructors)
    temp = []
    for i in instructors:
        self.append(
            "table_vwbr",
            {
                "school": "".join(i.get("program").split("-")[1::]),
                "teacher": i.get("parent"),
                "division": i.get("student_group"),
            },
        )

    self.table_vwbr = get_unique_cmap_assignees(self.table_vwbr)


def generate_text_from_unique_notes(self, type, added_broadcasts):
    if check_if_note_added_unique(type, added_broadcasts):
        frappe.errprint(added_broadcasts)
        descriptions = frappe.db.get_list(
            "Item CMAP Material",
            filters=[["name", "in", added_broadcasts]],
            fields=["description", "description"],
            ignore_permissions=True,
        )
        self.broadcast_text = "\\n".join(
            [item.get("description") for item in descriptions]
        )


@frappe.whitelist()
def check_if_note_added_unique(material_type, added_items):
    flag = True
    added_items = parse_json(added_items)
    frequency_counter = {}
    for item in added_items:
        frequency_counter[item] = frequency_counter.get(item, 0) + 1

    cmap_materials = frappe.db.get_list(
        "Item CMAP Material",
        filters=[
            ["material_type", "=", material_type],
            ["name", "in", added_items],
        ],
        fields=[
            "name",
            "name",
            "description",
            "description",
            "material_type",
            "material_type",
        ],
        ignore_permissions=True,
    )
    frappe.errprint(cmap_materials)
    index_dict = {}

    for i, item in enumerate(cmap_materials):
        description = item["description"]
        name = item["name"]
        if description in index_dict:
            index_dict[description].append(name)
        else:
            index_dict[description] = [name]
    frappe.errprint(index_dict)

    for i in index_dict:
        for j in index_dict[i]:
            if frequency_counter.get(j) > 1:
                flag = False
                frappe.msgprint(
                    f"Description {i} or Doc is same for {material_type} doc named {','.join(index_dict.get(i))}"
                )

    return flag


def get_unique_cmap_assignees(data_list):
    unique_combinations = set()

    unique_items = []

    for item in data_list:
        combination = (item.get("school"), item.get("division"), item.get("teacher"))

        if combination not in unique_combinations:
            unique_combinations.add(combination)
            unique_items.append(item)

    return unique_items


@frappe.whitelist(allow_guest=True)
def get_cmap_assignees_report(**filters):
    cmap_table = frappe.qb.DocType("CMAP")
    instructor_log_table = frappe.qb.DocType("Instructor Log")
    instructor_table = frappe.qb.DocType("Instructor")

    # cmap_assignment_table = frappe.qb.DocType("CMAP Assignment")
    # student_group_table = frappe.qb.DocType("Student Group")

    query = (
        frappe.qb.from_(cmap_table)
        .inner_join(instructor_log_table)
        .on((instructor_table.academic_year == cmap_table.academic_year))
        .select("*")
    )
    return query.run(as_dict=True)


@frappe.whitelist()
def get_cmap_period_no(self):
    self = json.loads(self) if isinstance(self, str) else self
    if not self.get("subject") or not self.get("academic_year"):
        return

    max_period_list = frappe.db.get_list(
        "CMAP",
        filters={
            "subject": self.get("subject"),
            "academic_year": self.get("academic_year"),
            "class": self.get("class"),
        },
        fields=["MAX(period)"],
    )

    max_period = max_period_list[0].get("MAX(period)", 0)
    if not self.get("period") and not max_period:
        return 1
    elif str(self.get("period")) == max_period or not self.get("period"):
        return int(max_period) + 1


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_unique_material_query(doctype, txt, searchfield, start, page_len, filters):
    materials = frappe.db.get_list(
        doctype=doctype,
        filters=filters,
        start=start,
        page_length=page_len,
        as_list=True,
        ignore_permissions=True,
        fields=["name", "description"],
    )
    merged_array = []
    merged_dict = {}
    for key, value in materials:
        if value not in merged_dict:
            merged_dict[value] = key
            merged_array.append((key, value))

    return merged_array


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_current_and_next_year(doctype, txt, searchfield, start, page_len, filters):
    acad_year_table = frappe.qb.DocType("Academic Year")

    query = (
        frappe.qb.from_(acad_year_table)
        .where(
            (acad_year_table.custom_current_academic_year == 1)
            | (acad_year_table.custom_next_academic_year == 1)
        )
        .select(acad_year_table.name)
    )

    return query.run()
