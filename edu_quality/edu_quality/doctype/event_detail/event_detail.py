# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EventDetail(Document):

    def on_update(self):
        self.update_classes()

    def update_classes(self):
        event = frappe.get_doc("Event", self.event)
        for cls in event.custom_classes:
            if not frappe.db.exists(
                "Classes", {"parent": self.name, "class": cls.get("class")}
            ):
                self.append("classes_applicable_to", {"class": cls.get("class")})

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

    def add_allowed_students(self):
        if not self.auto_add_students:
            return

        # Prepare a list to gather all students at once, reducing the number of database queries
        student_status = [i.student_status for i in self.student_status]
        all_students = []
        for cls in self.classes_applicable_to:
            students = frappe.get_all(
                "Student",
                filters={
                    "student_status": ["in", student_status],
                    "program": cls.get("class"),
                },
                fields=["name", "student_name", "reference_number"],
            )
            all_students.extend(students)

        # Prepare a set of existing event student references to minimize individual checks
        existing_students = set(
            frappe.get_all(
                "Event Student",
                filters={
                    "parent": self.name,
                    "parentfield": "allowed_students",
                },
                pluck="student",
            )
        )

        # Add students only if they do not already exist
        for student in all_students:
            if student.name not in existing_students:
                frappe.get_doc(
                    {
                        "doctype": "Event Student",
                        "parent": self.name,
                        "parenttype": "Event Detail",
                        "parentfield": "allowed_students",
                        "student": student.name,
                        "student_name": student.student_name,
                        "refno": student.reference_number,
                    }
                ).insert(ignore_permissions=True)
        self.reload()


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
