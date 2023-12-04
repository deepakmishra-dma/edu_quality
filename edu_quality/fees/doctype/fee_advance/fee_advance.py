# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

from edu_quality.public.py.fee import payment_split
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today
from edu_quality.overrides import make_payment_request


class FeeAdvance(Document):
    def autoname(self):
        self.name = self.student + " - " + self.fee_structure

    def before_save(self):
        if self.is_rte:
            fee_structure = frappe.get_doc("Fee Structure", self.fee_structure)
            self.components = []
            percent = get_percent(self.payment_term, self.payment_plan)
            amount = 0
            for component in fee_structure.components:
                amount += component.amount * percent / 100
                self.append(
                    "components",
                    {
                        "fees_category": component.fees_category,
                        "description": component.description,
                        "amount": component.amount * percent / 100,
                    },
                )
            self.amount = amount
            self.outstanding_amount = amount
        else:
            fee_structure = frappe.get_doc("Fee Structure", self.fee_structure)
            percent = get_percent(self.payment_term, self.payment_plan)
            amount = 0
            self.components = []
            for component in fee_structure.components:
                amount += component.amount * percent / 100
            self.amount = amount
            self.outstanding_amount = amount

    def before_submit(self):
        payment_split(self)

    
    
    def on_submit(self):
        student_email = frappe.db.get_value("Student", self.student, "student_email_id")
        make_payment_request(
                party_type="Student",
                party=self.student,
                dt=self.doctype,
                dn=self.name,
                recipient_id=student_email,
                submit_doc=True,
            )


def get_percent(term, payment_plan):
    doc = frappe.get_doc("Payment Plan", payment_plan)
    for d in doc.payment_schedule:
        if d.payment_term == term:
            return d.invoice_portion
    return 100

    
@frappe.whitelist()
def fee_advance(**kwargs):
    students = kwargs.get("students")
    students = frappe.parse_json(students)
    for s in students:
        student = frappe.get_doc("Student", s.get("name"))
        if frappe.db.exists("Program Enrollment", {"student": student.name}):
            program_enrollment = frappe.get_doc("Program Enrollment", {"student": student.name})
            create_fee_advance(student, program_enrollment)
        else:
            frappe.msgprint(
                f"Program Enrollment does not exists for student <b>{student.first_name}</b>. Fee Advance can only be created for old students."
            )


def create_fee_advance(student, program_enrollment):
    """
    program_enrollment: Previous Program Enrollment Doc
    """
    school = frappe.get_value("Program", program_enrollment.program, ["school"])
    institution = frappe.get_value("School", school, ["institution"])
    next_program = get_next_program(program_enrollment.program, school)
    academic_year = get_current_academic_year()
    fee_structure = get_fee_structure(academic_year, school, next_program)
    payment_plan = get_payment_plan(fee_structure, program_enrollment)

    fee_advance = frappe.new_doc("Fee Advance")
    fee_advance.student = program_enrollment.student
    fee_advance.academic_year = academic_year
    fee_advance.school = school
    fee_advance.fee_structure = fee_structure
    fee_advance.institution = institution
    fee_advance.program = program_enrollment.program
    fee_advance.next_program = next_program
    fee_advance.payment_plan = payment_plan
    fee_advance.payment_term = get_first_payment_term(payment_plan)
    fee_advance.is_rte = student.is_rte
    fee_advance.posting_date = today()
    fee_advance.due_date = frappe.utils.add_days(today(), 30)
    fee_advance.save()
    fee_advance.submit()
    frappe.msgprint(
        f"Fee Advance created for student <b>{student.first_name}</b>."
    )

def get_next_program(program, school):
    program_name = frappe.get_value("Program", program, "program_name")
    next_program = int(program_name) + 1
    next_program = frappe.get_value("Program", {"program_name": str(next_program), "school":school})
    return next_program


def get_first_payment_term(payment_plan):
    payment_plan = frappe.get_doc("Payment Plan", payment_plan)
    return payment_plan.payment_schedule[0].payment_term


def get_fee_structure(academic_year, school, program):
    doc_filter = {"academic_year": academic_year, "school": school, "program": program}
    fee_structure = frappe.get_value("Fee Structure", doc_filter)
    return fee_structure


def get_current_academic_year():
    from datetime import datetime
    acads = frappe.get_list("Academic Year")
    for acad in acads:
        doc = frappe.get_doc("Academic Year", acad.name)
        today_date = datetime.strptime(today(), "%Y-%m-%d").date()
        if doc.year_start_date <= today_date <= doc.year_end_date:
            return acad.name
    return None


def get_payment_plan(fee_structure=None, program_enrollment=None):
    if fee_structure:
        payment_plan = frappe.get_value("Payment Plan", {"fee_structure": fee_structure}, "name")
        if payment_plan:
            return payment_plan

    program_enrollment.custom_payment_plan