# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EventDetail(Document):

    def before_save(self):
        self.update_classes()

    def update_classes(self):
        event = frappe.get_doc("Event", self.event)
        # Get the existing classes
        existing_classes = frappe.db.get_all(
            "Classes", filters={"parent": self.name}, pluck="class"
        )
        # Remove classes that are no longer applicable
        self.classes_applicable_to = []

        # Add new applicable classes
        for cls in event.custom_classes:
            class_name = cls.get("class")
            if class_name not in existing_classes:
                self.append("classes_applicable_to", {"class": class_name})

    @frappe.whitelist()
    def get_students(self, args):
        refno = args.get("reference_number")
        student_status = args.get("student_status")
        students = []
        if refno:
            school = args.get("school")
            refno_list = refno.split(",")
            students = frappe.get_all(
                "Student",
                filters={
                    "reference_number": ["in", refno_list],
                    "school": school,
                    "student_status": student_status,
                },
                fields=["name", "student_name"],
            )
            print(students, school, refno_list)
        return students

    @frappe.whitelist()
    def send_registration_link(self, data):
        data = frappe.parse_json(data)
        base_url = frappe.utils.get_url() + "/event-registration-form/"
        for d in data:
            registration_url = base_url + d.get("name")
            student = frappe.get_doc("Student", d.get("student"))
            frappe.sendmail(
                recipients=student.student_email_id,
                subject="Registration Link",
                message=f"Click on the link to register for the event: {registration_url}",
            )
        return True


@frappe.whitelist()
def add_participating_students(student_data):
    student_data = frappe.parse_json(student_data)
    parent_name = student_data.get("parent")
    student = student_data.get("student")
    parent_doc = frappe.get_doc("Event Detail", parent_name)
    if not frappe.db.exists(
        "Student Data",
        {
            "student": student,
            "parent": parent_name,
            "parentfield": "participating_students",
        },
    ):
        parent_doc.append(
            "participating_students",
            {
                "student": student_data.get("student"),
                "student_name": student_data.get("student_name"),
                "refno": student_data.get("refno"),
            },
        )
        parent_doc.save()
        return True
    return False
