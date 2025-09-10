# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EventDetails(Document):

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
