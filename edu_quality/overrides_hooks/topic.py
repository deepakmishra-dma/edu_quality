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


def before_insert(self, method=None):
    chapter_number = 1
    list_topics = frappe.db.get_list(
        "Topic",
        fields=["custom_chapter_number"],
        filters=[
            ["custom_textbook", "=", self.custom_textbook],
            ["custom_subject", "=", self.custom_subject],
            ["custom_class", "=", self.custom_class],
        ],
        order_by="custom_chapter_number DESC",
        ignore_permissions=True,
    )


def after_insert(self, method=None):
    subject = frappe.get_doc("Course", self.custom_subject)
    subject.append("topics", {"topic": self.topic_name, "topic_name": self.topic_name})
    subject.save()
