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
    syllabus = subject.get("custom_syllabus")
    language = subject.get("custom_language")
    class_name = subject.get("custom_class")
    subject_short_code = subject.get("custom_short_code")
    syllabus_code = "C" if syllabus == "CBSE" else "S"
    language_short_code = "E" if language == "English" else "M"
    chapter_code = self.custom_chapter_name
    sheet_number = self.custom_sheet_number
   
    self.item_code = strip(
        short_code
        + language_short_code
        + syllabus_code
        + class_name
        + subject_short_code
        + chapter_code
        + sheet_number
    )

    self.name = self.item_code
    self.item_name = self.item_code
