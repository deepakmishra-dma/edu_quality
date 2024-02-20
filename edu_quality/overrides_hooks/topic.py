import frappe


def autoname(self, method=None):
    course_shortcode = frappe.db.get_value(
        "Course", self.custom_subject, "custom_short_code"
    )
    textbook_shortcode = frappe.db.get_value(
        "Textbook", self.custom_textbook, "short_code"
    )
    class_shortcode = frappe.db.get_value("Class Type", self.custom_class, "short_code")
    self.name = f"{course_shortcode}{textbook_shortcode}{class_shortcode}{self.custom_chapter_number} - {self.topic_name}"



def after_insert(self, method=None):
    subject = frappe.get_doc("Course", self.custom_subject)
    subject.append("topics", {"topic": self.topic_name, "topic_name": self.topic_name})
    subject.save()
