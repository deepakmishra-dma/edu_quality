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
            self.append("classes_applicable_to", {"class": cls.get("class")})

    @frappe.whitelist()
    def get_students(self, args):
        program = args.get("program")
        division = args.get("division")
        refno = args.get("reference_number")
        students = []
        if program:
            students = frappe.get_all(
                "Student",
                filters={"program": program, "student_status": ["!=", "Cancelled"]},
                pluck="name",
            )
        if division:
            students = frappe.get_all(
                "Program Enrollment",
                filters={
                    "student_group": division,
                    "custom_status": ["!=", "Cancelled"],
                },
                pluck="student",
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
                pluck="name",
            )
        return students
