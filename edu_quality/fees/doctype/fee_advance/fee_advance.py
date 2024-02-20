# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import json
from edu_quality.public.py.discount import calculate_discount, get_discount_list
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

from edu_quality.common.utils.progress import set_progress
from edu_quality.edu_quality.server_scripts.payment_split import generate_split_payment


class FeeAdvance(AccountsController):
    def generate_split(self):
        generate_split_payment(self)

    def update_split(self):
        generate_split_payment(self,update=1)


    def before_save(self):
        percent = get_percent(self.payment_term, self.payment_plan)
        components, amount = get_components(self.fee_structure, percent, self.is_rte)
        self.amount = amount
        self.outstanding_amount = amount
        self.components = []
        for component in components:
            self.append('components', component)

    def before_submit(self):
        referal_discount(self, "Before Submit")
        self.generate_split()

    def validate(self):
        self.set_missing_accounts_and_fields()

    
    def on_submit(self):
        self.make_gl_entries()

        student_email = frappe.db.get_value("Student", self.student, "student_email_id")
        today_date = frappe.utils.getdate(today())

        if isinstance(self.due_date, str):
            due_date = frappe.utils.getdate(self.due_date)
        else:
            due_date = self.due_date

        if (due_date - today_date).days < 30:
            make_payment_request(
                    party_type="Student",
                    party=self.student,
                    dt=self.doctype,
                    dn=self.name,
                    recipient_id=student_email,
                    payment_term=self.payment_term,
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
            company = frappe.get_value("Program", self.next_program,"school")
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
            student_entries = {}
            fee_entries = {}

            for component in self.components:
                company = component.custom_company or self.company
                receivable_account, liability_account, cost_center = frappe.db.get_value("Company", company, ["default_receivable_account", "default_liability_account", "cost_center"])

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
            return entries
        except Exception as e:
            frappe.logger('fee').exception(e)


def get_components(fee_structure, percent, is_rte):
    fee_structure_doc = frappe.get_doc("Fee Structure", fee_structure)
    components = []
    amount = 0
    for component in fee_structure_doc.components:
        if is_rte:
            rte_excempt = frappe.get_value("Fee Category",component.fees_category, "rte_excempt")
            if rte_excempt:
                continue
        label = frappe.get_value("Fee Category",component.fees_category, "custom_label")
        default_account = frappe.get_value("Fees Settings", None, "default_account")

        component_amount = component.amount * percent / 100
        amount += component_amount
        components.append(
            {
                "fees_category": component.fees_category,
                "description": component.description,
                "amount": component_amount,
                "custom_company": component.custom_company,
                "label": label or default_account,
                "custom_company": component.custom_company,
                "fee_type": component.fee_type,
            }
        )
    return components, amount


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


def create_fee_advance(student, program_enrollment,all_len=None,index=None):
    """
    program_enrollment: Previous Program Enrollment Doc
    """
    try:
        if frappe.get_value("Program", program_enrollment.program, "custom_is_passing_out_class"):
            frappe.log_error(title="Fee Advance",message="Since there is not a class scheduled for {class_name}, we will not be creating a fee advance.".format(class_name =program_enrollment.program))
            return 
        if all_len and index:
            set_progress(index + 1, all_len,index, "Student Fees Details")
        school = frappe.get_value("Program", program_enrollment.program,"school")
        next_program = get_next_program(program_enrollment.program, school)
        institution = frappe.get_value("School", frappe.get_value("Program", next_program,"school"),"institution")
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
        fee_advance.receivable_account = frappe.get_value("Company", institution, "default_receivable_account")
        fee_advance.income_account = frappe.get_value("Company", institution, "default_liability_account")
        fee_advance.cost_center = frappe.get_value("Company", institution, "cost_center")
        fee_advance.save()
        fee_advance.submit()
    except Exception:
        frappe.log_error(
            title="Fee Advance",
            message=frappe.get_traceback(),
        )

def get_next_program(program, school):
    sequence = frappe.get_value("Program", program, "sequence")
    next_program = int(sequence) + 1
    next_program = frappe.get_value("Program", {"sequence": str(next_program), "school":school})
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
    if program_enrollment.payment_plan:
        return program_enrollment.payment_plan
    payment_plan = frappe.get_value("Payment Plan", {"fee_structure": fee_structure,"plan_name":["like", "%P2%"]}, "name")
    if payment_plan:
        return payment_plan
    else:
        return frappe.get_value("Payment Plan", {"fee_structure": fee_structure}, "name")


def referal_discount(doc, method=None):
    """
    Apply referral discount to eligible fee components and update the document when creating fee document.

    Parameters:
    - doc (frappe.model.document.Document): The document to which the referral discount is applied.
    - method (str, optional): The method triggering the referral discount application.

    Returns:
    dict: A dictionary containing information about the applied referral discount per fee category.
    """
    grand_total = doc.amount
    student = frappe.get_doc("Student", doc.student)

    if student.is_rte or student.referral_amount == 0:
        return
    
    discount = float(student.referral_amount)

    for component in doc.components:
        if not component.fees_category != "Tuition Fee":
            continue

        if component.amount > discount and discount != 0:
            amount = component.custom_amount_after_discount or component.amount
            amount_after_discount = amount - discount
            previous_discount = component.custom_discount_amount or 0
            new_discount = previous_discount + discount
            discount_percentage = calculate_discount(component.amount, new_discount)

            discount_name = component.custom_discounts
            discount_list = get_discount_list(discount_name)

            if discount_list and "Referral" not in discount_list:
                discount_list.append("Referral")
                discount_name = ", ".join(discount_list)
            else:
                discount_name = "Referral"

            grand_total = doc.amount - discount

            if method == "Before Submit":
                component.custom_discounts = discount_name
                component.custom_discount_amount = new_discount
                component.custom_amount_after_discount = amount_after_discount
                component.custom_discount_percentage = discount_percentage

                doc.amount = grand_total
                doc.outstanding_amount = grand_total

            elif method == "Before Update":
                updates = {
                    "custom_discounts": discount_name,
                    "custom_discount_amount": new_discount,
                    "custom_amount_after_discount": amount_after_discount,
                    "custom_discount_percentage": discount_percentage
                }

                frappe.db.set_value("Fee Component", component.name, updates)

                doc_updates = {
                    "amount": grand_total,
                    "outstanding_amount": doc.outstanding_amount - discount
                }

                frappe.db.set_value("Fee Advance", doc.name, doc_updates)  
            break  