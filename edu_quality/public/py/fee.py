from edu_quality.public.py.discount import payment_plan, referal_discount, time_based_discount, update_payment_schedule
import frappe 
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_company_defaults,
    get_payment_entry,
)
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from frappe.utils import flt, get_url, nowdate
from edu_quality.overrides import make_payment_request
from datetime import datetime
from edu_quality.public.py.payment_request import update_payment_request_after_discount

def after_insert(doc,method=None):
    payment_plan(doc)

def before_submit(doc,method=None):
    time_based_discount(doc)
    referal_discount(doc)
    update_payment_schedule(doc)


def before_update(doc,method=None):    
    old_doc = doc.get_doc_before_save()
    if old_doc.payment_schedule != doc.payment_schedule:
        ps = []
        for term,old_term in zip(doc.payment_schedule,old_doc.payment_schedule):
            if old_term.outstanding == 0 and term.outstanding != 0:
                frappe.throw("Cannot Change term - " + term.payment_term + " As it is already Paid!")
            if term.invoice_portion:
                term.payment_amount = (term.invoice_portion * doc.grand_total)/100
            elif term.payment_amount:
                term.invoice_portion = (term.payment_amount/doc.grand_total)*100
            ps.append(term)
        doc.payment_schedule = ps
        update_payment_request_after_discount(doc)

def before_save(doc,method=None):
    try:
        if not doc.get("school"):
            doc.school = frappe.db.get_value("Student",doc.student,"school")
        old = doc.get_doc_before_save()
        if old.workflow_state != doc.workflow_state:
            update_payment_schedule(doc)
            update_payment_request_after_discount(doc)
    except Exception as e:
        frappe.logger("fee").exception(e)

def create_fees(doc,method=None):
    try:
        doc = frappe.get_doc("Student",doc.student)
        if doc.student_applicant:
            student_applicant = frappe.get_doc("Student Applicant",doc.student_applicant)
            fees = frappe.get_doc({
                "doctype": "Fees",
                "student": doc.name,
                "program_enrollment": frappe.db.get_value("Program Enrollment",{'student': doc.name},'name'),
                "fee_structure": student_applicant.fee_structure,
                "fee_schedule": student_applicant.fee_schedule,
                "company": student_applicant.institution
            })
            # if student_applicant.application_fees:
            #     fees.append("components",{
            #         'fees_category':"Application Fees",
            #         'amount':student_applicant.application_fees
            #     })
            if len(student_applicant.fee_components) > 0:
                for component in student_applicant.fee_components:
                    fees.append("components",{
                        'fees_category':component.fees_category,
                        'amount':component.amount,
                        'description': component.description
                    })
            else:
                fee_structure = frappe.get_doc("Fee Structure",student_applicant.fee_structure) 
                for component in fee_structure.components:
                    fees.append("components",{
                        'fees_category':component.fees_category,
                        'amount':component.amount,
                        'description': component.description
                    })
            fees.insert()
            fees.submit()
            from edu_quality.public.py.student import update_student_group
            update_student_group(fees.program_enrollment,fee_structure=student_applicant.fee_structure)
    except Exception as e:
        frappe.throw(str(e))



class CustomPaymentRequest(PaymentRequest):
    def create_payment_entry(self,submit=True):
        if not  self.reference_doctype == 'Fees':
            return
        frappe.flags.ignore_account_permission = True

        ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
        company = frappe.get_doc("Company", ref_doc.company)
        party_account = company.default_receivable_account
        party_account_currency = get_account_currency(party_account)
        deposits = 0
        fees = 0
        for component in ref_doc.components:
            if frappe.db.exists("Security Deposit",component.fees_category):
                        deposits += component.amount
            else:
                fees += component.amount
        if deposits:
            frappe.logger('deposit').exception(deposits)
            payment_entry(self,ref_doc,deposits,deposits,company.default_payable_account)
        if fees:
            frappe.logger('deposit').exception(fees)
            return payment_entry(self,ref_doc,fees,fees,company.default_receivable_account)
        

def payment_entry(doc,ref_doc,bank_amount,party_amount,paid_to):
    bank_amount = doc.grand_total
    party_amount = doc.grand_total

    payment_entry = frappe.get_doc({
        'doctytpe': "Payment Entry",
        'payment_type': 'Receive',
        'company': ref_doc.company,
        'cost_center': doc.get("cost_center"),
        'posting_date': nowdate(),
        'reference_date': nowdate(),
        'mode_of_payment': doc.get("mode_of_payment"),
        'party_type': "Student",
        'party': ref_doc.student,
        'party_name': frappe.get_value("Student",ref_doc.student,'first_name'),
        'paid_to': paid_to,
        'paid_amount': party_amount,
        

    })

    payment_entry.update(
        {
            "mode_of_payment": doc.mode_of_payment,
            "reference_no": doc.name,
            "reference_date": nowdate(),
            "remarks": "Payment Entry against {0} {1} via Payment Request {2}".format(
                doc.reference_doctype, doc.reference_name, doc.name
            ),
        }
    )

    # Update dimensions
    payment_entry.update(
        {
            "cost_center": doc.get("cost_center"),
            "project": doc.get("project"),
        }
    )

    for dimension in get_accounting_dimensions():
        payment_entry.update({dimension: doc.get(dimension)})

    if payment_entry.difference_amount:
        company_details = get_company_defaults(ref_doc.company)

        payment_entry.append(
            "deductions",
            {
                "account": company_details.exchange_gain_loss_account,
                "cost_center": company_details.cost_center,
                "amount": payment_entry.difference_amount,
            },
        )

    payment_entry.insert(ignore_permissions=True)
    payment_entry.submit()
    return payment_entry


@frappe.whitelist()
def get_due_date(fee):
    fee = frappe.get_doc("Fees",fee)
    due_date = ""
    for term in fee.payment_schedule:
        if not due_date:
            due_date = term.due_date
        if frappe.db.exists("Payment Request",{'payment_term':term.payment_term,"reference_name":fee.name}):
            due_date = term.due_date
    return due_date


