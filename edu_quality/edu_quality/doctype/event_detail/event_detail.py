# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EventDetail(Document):

    def on_update(self):
        self.update_classes()

    def update_classes(self):
        cal_doc = frappe.get_doc("Calender", self.calendar_event_name)
        for cls in cal_doc.classes_applicable_to:
            if not frappe.db.exists(
                "Classes", {"parent": self.name, "class": cls.get("class")}
            ):
                self.append("classes_applicable_to", {"class": cls.get("class")})

    @frappe.whitelist()
    def get_students(self, args):
        program = args.get("program")
        division = args.get("division")
        refno = args.get("reference_number")
        students = []
        if program:
            student_status = args.get("student_status")
            program = [program.get("class") for program in program]
            students = frappe.get_all(
                "Student",
                filters={"program": ["in", program], "student_status": student_status},
                fields=["name", "student_name"],
            )
        if division:
            students = frappe.db.sql(
                """
                SELECT student.name, student.student_name FROM `tabStudent` as student
                JOIN `tabProgram Enrollment` as program_enrollment ON student.name = program_enrollment.student
                WHERE program_enrollment.student_group = %s
                AND program_enrollment.custom_status != 'Cancelled'
            """,
                division,
                as_dict=True,
            )
        if refno:
            school = args.get("school")
            refno_list = refno.split(",")
            students = frappe.get_all(
                "Student",
                filters={
                    "reference_number": ["in", refno_list],
                    "school": school,
                    "student_status": ["!=", "Cancelled"],
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
    parent_doc = frappe.get_doc("Event Details", parent_name)
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
