import frappe
from frappe.utils import strip
import json


@frappe.whitelist()
def name(self):
    self = json.loads(self) if isinstance(self, str) else self

    if not self.get("item_group"):
        return

    current_item_group = frappe.get_doc("Item Group", self.get("item_group"))
    if current_item_group.get("parent_item_group") != "CMAP":
        return

    short_code = current_item_group.custom_group_code
    subject = frappe.get_doc("Course", self.get("custom_subject"))
    textbook = frappe.get_doc("Textbook", self.get("custom_textbook"))
    chapter = frappe.get_doc("Topic", self.get("custom_chapter"))
    syllabus = subject.get("custom_syllabus")
    language = subject.get("custom_language")
    class_name = self.get("custom_class")
    textbook_short_code = textbook.get("short_code")

    syllabus_code = "C" if syllabus == "CBSE" else "S"
    language_short_code = "E" if language == "English" else "M"
    chapter_code = chapter.get("custom_chapter_number")
    sheet_number = self.get("custom_sheet_number")
    item_code = strip(
        f"{short_code}{language_short_code}{syllabus_code}{class_name}{textbook_short_code}{str(chapter_code).zfill(2)}{str(sheet_number).zfill(2)}"
    )
    return item_code


def autoname(self, method=None):
    self.item_code = name(self)
    self.name = self.item_code
    self.item_name = self.item_code


@frappe.whitelist()
def calculate_sheet_number(self):
    self = json.loads(self) if isinstance(self, str) else self
    if not self.get("item_group"):
        return

    current_item_group = frappe.get_doc("Item Group", self.get("item_group"))
    if current_item_group.get("parent_item_group") != "CMAP":
        return

    sheet_number = 1
    list_topics = frappe.db.get_list(
        "Item",
        fields=["custom_sheet_number"],
        filters=[
            ["custom_is_cmap", "=", 1],
            ["item_group", "=", self.get("item_group")],
            ["custom_textbook", "=", self.get("custom_textbook")],
            ["custom_subject", "=", self.get("custom_subject")],
            ["custom_class", "=", self.get("custom_class")],
            ["custom_chapter", "=", self.get("custom_chapter")],
        ],
        limit=1,
        order_by="custom_sheet_number DESC",
        ignore_permissions=True,
    )
    frappe.errprint(list_topics)
    if list_topics and len(list_topics):
        sheet_number = list_topics[0].get("custom_sheet_number") + 1
    return sheet_number


def before_insert(self, method=None):
    self.custom_sheet_number = calculate_sheet_number(self)
