# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder.functions import Count
from frappe.utils import parse_json
import json
from edu_quality.public.py.utils import check_admin_roles
import string
import random

# edu_quality.edu_quality.doctype.cmap.cmap


class CMAP(Document):
    def name_func(self):
        course_short_code = frappe.db.get_value(
            "Course", self.subject, "custom_short_code"
        )
        course_doc = frappe.get_doc("Course", self.subject)
        class_sortcode = frappe.db.get_value(
            "Class Type", self.get("class"), "short_code"
        )
        self.name = f"{self.academic_year}-{course_short_code}{class_sortcode}{self.unit}{self.period}"
        return self.name

    def autoname(self, method=None):
        self.name_func()

    def before_validate(self, method=None):

        added_broadcasts = [product.get("broadcast") for product in self.products] or []
        added_parent_notes = [
            product.get("parent_note") for product in self.products
        ] or []
        added_home_works = [product.get("home_work") for product in self.products] or []
        added_material_required = [
            product.get("material_required") for product in self.products
        ] or []
        added_class_works = [
            product.get("class_work") for product in self.products
        ] or []
        generate_text_from_unique_notes(
            self, "Broadcast", added_broadcasts, field="broadcast_text"
        )
        generate_text_from_unique_notes(
            self, "Parent Note", added_parent_notes, field="parent_notes"
        )
        generate_text_from_unique_notes(
            self, "Home Work", added_home_works, field="home_work"
        )
        generate_text_from_unique_notes(
            self, "Class Work", added_class_works, field="class_work"
        )
        generate_text_from_unique_notes(
            self,
            "Material Required",
            added_material_required,
            field="material_required",
        )

        self.item_code_field = ", ".join(item.get("item", "") for item in self.products)

    def after_insert(self, method=None):
        insert_cmap_assignees(self)

    def on_update(self, method=None):
        old_doc = self.get_doc_before_save()
        if (
            old_doc
            and (self.reserved_for_portion_circular
            != old_doc.reserved_for_portion_circular
            or self.period != old_doc.period)
        ):
            frappe.rename_doc("CMAP", old_doc.name, self.name_func())


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


def generate_text_from_unique_notes(self, type, added_broadcasts, field):
    if field is None:
        return
    if check_if_note_added_unique(type, added_broadcasts):

        setattr(
            self,
            field,
            "\\n".join([item or "" for item in added_broadcasts]),
        )


@frappe.whitelist()
def check_if_note_added_unique(material_type, added_items=[]):
    flag = True
    added_items = parse_json(added_items)
    frequency_counter = {}
    for item in added_items:
        frequency_counter[item] = (frequency_counter.get(item, 0) or 0) + 1

    index_dict = {}

    for description in added_items:
        if description in index_dict:
            index_dict[description].append(description)
        else:
            index_dict[description] = [description]

    for i in index_dict:
        for j in index_dict[i]:
            if frequency_counter.get(j) > 1:
                if i == None or not i:
                    continue
                flag = False
                frappe.msgprint(f"Description {i} or Doc is same for {material_type} ")

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
            "reserved_for_portion_circular": 0,
        },
        fields=["MAX(period)"],
    )

    max_period = max_period_list[0].get("MAX(period)", 0)
    if not self.get("period") and not max_period or isinstance(max_period, str):
        return 1
    elif str(self.get("period")) == max_period or not self.get("period"):
        return int(max_period) + 1


@frappe.whitelist()
def get_unique_material_query(filters):
    filters = json.loads(filters) if isinstance(filters, str) else filters
    materials = frappe.db.get_list(
        doctype="Item CMAP Material",
        filters=filters,
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


field_map = {
    "Material Required": "material_required",
    "Broadcast": "broadcast",
    "Home Work": "home_work",
    "Parent Note": "parent_note",
    "Class Work": "class_work",
}


def calculate_product_materials(name):
    cmap_doc = frappe.get_doc("CMAP", name)
    products = cmap_doc.get("products", [])
    product_names = [i.get("item") for i in products]
    item_table = frappe.qb.DocType("Item")
    material_table = frappe.qb.DocType("Item CMAP Material")

    # only return products having one material to minimize looping and updates
    query = (
        frappe.qb.from_(item_table)
        .inner_join(material_table)
        .on(material_table.parent == item_table.name)
        .where((item_table.name.isin(product_names)))
        .groupby(item_table.name, material_table.material_type)
        .having(Count(material_table.name) == 1)
        .select(
            material_table.name.as_("material_name"),
            item_table.name.as_("item_name"),
            material_table.material_type,
            material_table.description,
        )
    )
    data = query.run(as_dict=True)
    try:
        product_hash = {}
        for i in data:
            item = i.get("item_name")
            if item not in product_hash:
                product_hash[item] = [i]
            else:
                product_hash[item].append(i)

        for product in products:
            item = product.item
            if item in product_hash:
                for material in product_hash[item]:
                    frappe.db.set_value(
                        "Item Detail",
                        product.name,
                        field_map.get(material.get("material_type")),
                        material.get("description", ""),
                    )
    except Exception as e:
        frappe.log_error(
            f"Error while calculating Product Material for {name}",
            frappe.get_traceback(),
        )


# edu_quality.edu_quality.doctype.cmap.cmap.calculate_all_product_materials
@frappe.whitelist()
def calculate_all_product_materials():
    user_roles = frappe.get_roles(frappe.session.user)
    is_admin = check_admin_roles(user_roles, ["Content Admin", "Content Creator"])
    if not is_admin:
        frappe.throw(("User Is not allowed to run this method"))
    cmaps = frappe.get_all("CMAP")
    for i in cmaps:
        frappe.enqueue(calculate_product_materials, name=i.get("name"), queue="long")


# edu_quality.edu_quality.doctype.cmap.cmap.get_product_materials
@frappe.whitelist()
def get_product_materials(item_id):
    item_doc = frappe.get_doc("Item", item_id, ignore_permissions=True)
    result = {}

    for material in item_doc.custom_additional_material:
        material_type = material.get("material_type")
        description = material.get("description")
        if material_type not in result:
            result[material_type] = [" ", description]
        # unique only
        elif result[material_type] and description not in result[material_type]:
            result[material_type].append(description)
    return result


@frappe.whitelist()
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))
