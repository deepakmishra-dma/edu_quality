# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import json
from edu_quality.public.py.fee import payment_split
from erpnext.accounts.doctype.account.account import get_account_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.accounts.utils import get_fiscal_years
import frappe
import erpnext
from erpnext.controllers.accounts_controller import (
    AccountsController,
    set_balance_in_account_currency,
    update_gl_dict_with_regional_fields,
)
from frappe.utils import today
from edu_quality.overrides import make_payment_request
from frappe.utils import (
    formatdate,
    today,
)

class FeeAdvance(AccountsController):
    def before_save(self):
        fee_structure = frappe.get_doc("Fee Structure", self.fee_structure)
        percent = get_percent(self.payment_term, self.payment_plan)
        self.components = []
        amount = 0

        for component in fee_structure.components:
            if self.is_rte:
                rte_excempt = frappe.get_value("Fee Category",component.fees_category, "rte_excempt")
                if rte_excempt:
                    continue

            component_amount = component.amount * percent / 100
            amount += component_amount
            self.append(
                "components",
                {
                    "fees_category": component.fees_category,
                    "description": component.description,
                    "amount": component_amount,
                    "custom_company": component.custom_company,
                },
            )

        self.amount = amount
        self.outstanding_amount = amount

    def before_submit(self):
        payment_split(self)

    def validate(self):
        self.set_missing_accounts_and_fields()

    
    def on_submit(self):
        self.make_gl_entries()

        student_email = frappe.db.get_value("Student", self.student, "student_email_id")
        make_payment_request(
                party_type="Student",
                party=self.student,
                dt=self.doctype,
                dn=self.name,
                recipient_id=student_email,
                submit_doc=True,
            )
    

    def on_cancel(self):
        if frappe.db.exists("Payment Request", {"reference_name": self.name}):
            doc = frappe.get_doc("Payment Request", {"reference_name": self.name})
            doc.cancel()
  

    def on_trash(self):
        if frappe.db.exists("Payment Request", {"reference_name": self.name}):
            doc = frappe.get_doc("Payment Request", {"reference_name": self.name})
            doc.delete()
    
        
    def set_missing_accounts_and_fields(self):
        if not self.company:
            company = frappe.get_value("Fee Structure", self.fee_structure, "institution")
            self.company = company
        if not self.currency:
            self.currency = erpnext.get_company_currency(self.company)
        if not (self.receivable_account and self.income_account and self.cost_center):
            accounts_details = frappe.get_all(
                "Company",
                fields=[
                    "default_receivable_account",
                    "default_income_account",
                    "default_liability_account",
                    "cost_center",
                ],
                filters={"name": self.company},
            )
            if accounts_details:
                accounts_details = accounts_details[0]
                if not self.receivable_account:
                    self.receivable_account = accounts_details.default_receivable_account
                if not self.income_account:
                    self.income_account = accounts_details.default_liability_account or accounts_details.default_income_account
                if not self.cost_center:
                    self.cost_center = accounts_details.cost_center


    def make_gl_entries(self):
        if not self.amount:
            return
        entries = self.get_company_splits()
        from erpnext.accounts.general_ledger import make_gl_entries

        make_gl_entries(
            entries,
            cancel=(self.docstatus == 2),
            update_outstanding="Yes",
            merge_entries=False,
        )


    def get_gl_dict(self, args, account_currency=None, item=None):
        """this method populates the common properties of a gl entry record"""
        company = args.get('company') or self.company
        posting_date = args.get("posting_date") or self.get("posting_date")
        fiscal_years = get_fiscal_years(posting_date, company=company)
        if len(fiscal_years) > 1:
            frappe.throw(
                frappe._("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
                    formatdate(posting_date)
                )
            )
        else:
            fiscal_year = fiscal_years[0][0]

        gl_dict = frappe._dict(
            {
                "company": company,
                "posting_date": posting_date,
                "fiscal_year": fiscal_year,
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "remarks": self.get("remarks") or self.get("remark"),
                "debit": 0,
                "credit": 0,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": 0,
                "is_opening": self.get("is_opening") or "No",
                "party_type": None,
                "party": None,
                "project": self.get("project"),
                "post_net_value": args.get("post_net_value"),
            }
        )

        update_gl_dict_with_regional_fields(self, gl_dict)
        accounting_dimensions = get_accounting_dimensions()
        dimension_dict = frappe._dict()

        for dimension in accounting_dimensions:
            dimension_dict[dimension] = self.get(dimension)
            if item and item.get(dimension):
                dimension_dict[dimension] = item.get(dimension)

        gl_dict.update(dimension_dict)
        gl_dict.update(args)

        if not account_currency:
            account_currency = get_account_currency(gl_dict.account)

        if gl_dict.account and self.doctype not in [
            "Journal Entry",
            "Period Closing Voucher",
            "Payment Entry",
            "Purchase Receipt",
            "Purchase Invoice",
            "Stock Entry",
        ]:
            self.validate_account_currency(gl_dict.account, account_currency)

        if gl_dict.account and self.doctype not in [
            "Journal Entry",
            "Period Closing Voucher",
            "Payment Entry",
        ]:
            set_balance_in_account_currency(
                gl_dict, account_currency, self.get("conversion_rate"), self.company_currency
            )

        return gl_dict


    def get_company_splits(self):
        try:
            receivable_account, liability_account, cost_center = frappe.db.get_value("Company", self.company, ["default_receivable_account", "default_liability_account", "cost_center"])
            student_entries = {}
            fee_entries = {}

            for component in self.components:
                if receivable_account not in student_entries:
                    student_entries[receivable_account] = self.get_gl_dict({
                        "company": component.custom_company,
                        "account": receivable_account,
                        "party_type": "Student",
                        "party": self.student,
                        "against": liability_account,
                        "debit": component.amount,
                        "debit_in_account_currency": component.amount,
                        "against_voucher": self.name,
                        "against_voucher_type": self.doctype
                    }, item=self)

                else:
                    student_entries[receivable_account]['debit'] += component.amount
                    student_entries[receivable_account]['debit_in_account_currency'] += component.amount

                if liability_account not in fee_entries:
                    fee_entries[liability_account] = self.get_gl_dict({
                        "company": component.custom_company,
                        "account": liability_account,
                        "against": self.student,
                        "credit": component.amount,
                        "credit_in_account_currency": component.amount,
                        "cost_center": cost_center
                    }, item=self)

                else:
                    fee_entries[liability_account]['credit'] += component.amount
                    fee_entries[liability_account]['credit_in_account_currency'] += component.amount

            entries = list(student_entries.values()) + list(fee_entries.values())
            frappe.logger('fee').exception(entries)
            return entries
        except Exception as e:
            frappe.logger('fee').exception(e)


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
        current_academic_year = frappe.get_value("Academic Year",{"custom_current_academic_year":1})
        pe_filter = {"student": student.name, "academic_year": current_academic_year}
        if frappe.db.exists("Program Enrollment", pe_filter):
            program_enrollment = frappe.get_doc("Program Enrollment", pe_filter)
            frappe.enqueue(create_fee_advance, student=student, program_enrollment=program_enrollment)
        else:
            frappe.msgprint(
                f"Program Enrollment does not exists for student <b>{student.first_name}</b>. Fee Advance can only be created for old students."
            )


def create_fee_advance(student, program_enrollment):
    """
    program_enrollment: Previous Program Enrollment Doc
    """
    try:
        school = frappe.get_value("Program", program_enrollment.program, ["school"])
        institution = frappe.get_value("School", school, ["institution"])
        next_program = get_next_program(program_enrollment.program, school)
        current_academic_year = frappe.get_value("Academic Year",{"custom_current_academic_year":1})
        next_academic_year = frappe.get_value("Academic Year",{"custom_next_academic_year":1})
        fee_structure = get_fee_structure(next_academic_year, school, next_program)
        payment_plan = get_payment_plan(fee_structure, program_enrollment)
        term, due_date = get_first_payment_term(payment_plan)

        fee_advance = frappe.new_doc("Fee Advance")
        fee_advance.student = program_enrollment.student
        fee_advance.academic_year = next_academic_year
        fee_advance.school = school
        fee_advance.fee_structure = fee_structure
        fee_advance.company = institution
        fee_advance.program = program_enrollment.program
        fee_advance.next_program = next_program
        fee_advance.payment_plan = payment_plan
        fee_advance.payment_term = term
        fee_advance.is_rte = student.is_rte
        fee_advance.posting_date = today()
        fee_advance.due_date = due_date
        fee_advance.is_rte = frappe.get_value("Student", program_enrollment.student, "is_rte_student")
        fee_advance.save()
        fee_advance.submit()
    except Exception:
        frappe.log_error(
            title="Fee Advance",
            message=frappe.get_traceback(),
        )

def get_next_program(program, school):
    program_name = frappe.get_value("Program", program, "program_name")
    next_program = int(program_name) + 1
    next_program = frappe.get_value("Program", {"program_name": str(next_program), "school":school})
    return next_program


def get_first_payment_term(payment_plan):
    payment_plan = frappe.get_doc("Payment Plan", payment_plan)
    term = payment_plan.payment_schedule[0].payment_term
    due_date = payment_plan.payment_schedule[0].due_date
    return term, due_date


def get_fee_structure(academic_year, school, program):
    doc_filter = {"academic_year": academic_year, "school": school, "program": program}
    fee_structure = frappe.get_value("Fee Structure", doc_filter)
    return fee_structure


def get_payment_plan(fee_structure=None, program_enrollment=None):
    if program_enrollment.custom_payment_plan:
        return program_enrollment.custom_payment_plan
    payment_plan = frappe.get_value("Payment Plan", {"fee_structure": fee_structure,"plan_name":["like", "%P2%"]}, "name")
    if payment_plan:
        return payment_plan
    else:
        return frappe.get_value("Payment Plan", {"fee_structure": fee_structure}, "name")
