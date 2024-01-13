import frappe
from frappe.utils import strip


def autoname(self, method=None):
    if not self.item_group:
        return

    current_item_group = frappe.get_doc("Item Group", self.item_group)
    if current_item_group.get("parent_item_group") != "CMAP":
        return

    short_code = current_item_group.custom_group_code
    subject = frappe.get_doc("Course", self.custom_subject)
    textbook = frappe.get_doc("Textbook", self.custom_textbook)
    chapter = frappe.get_doc("Topic", self.custom_chapter)
    syllabus = subject.get("custom_syllabus")
    language = subject.get("custom_language")
    class_name = self.get("custom_class")
    textbook_short_code = textbook.get("short_code")

    syllabus_code = "C" if syllabus == "CBSE" else "S"
    language_short_code = "E" if language == "English" else "M"
    chapter_code = chapter.get("custom_chapter_number")
    sheet_number = self.custom_sheet_number
    print(
        short_code,
        language_short_code,
        syllabus_code,
        class_name,
        textbook_short_code,
        str(chapter_code).zfill(2),
        str(sheet_number).zfill(2),
    )
    self.item_code = strip(
        f"{short_code}{language_short_code}{syllabus_code}{class_name}{textbook_short_code}{str(chapter_code).zfill(2)}{str(sheet_number).zfill(2)}"
    )

    self.name = self.item_code
    self.item_name = self.item_code


def before_insert(self, method=None):
    sheet_number = 1
    list_topics = frappe.db.get_list(
        "Item",
        fields=["custom_sheet_number"],
        filters=[
            ["custom_is_cmap", "=", 1]["custom_textbook", "=", self.custom_textbook],
            ["custom_subject", "=", self.custom_subject],
            ["custom_class", "=", self.custom_class],
            ["custom_chapter", "=", self.custom_chapter],
        ],
        limit=1,
        order_by="custom_sheet_number DESC",
        ignore_permissions=True,
    )
    if len(list_topics and len(list_topics[0])):
        sheet_number = list_topics[0][0] + 1

    self.custom_sheet_number = sheet_number
