# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import parse_json
import json


class CMAP(Document):
    def autoname(self, method=None):
        course_short_code = frappe.db.get_value(
            "Course", self.subject, "custom_short_code"
        )
        course_doc = frappe.get_doc("Course", self.subject)
        class_sortcode = frappe.db.get_value(
            "Class Type", self.get("class"), "short_code"
        )
        self.name = f"{self.academic_year}-{course_doc.name}{course_short_code}{class_sortcode}{self.unit}{self.period}"

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


def generate_text_from_unique_notes(self, type, added_broadcasts):
    if check_if_note_added_unique(type, added_broadcasts):
        frappe.errprint(added_broadcasts)
        descriptions = frappe.db.get_list(
            "Item CMAP Material",
            filters=[["name", "in", added_broadcasts]],
            fields=["description", "description"],
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
