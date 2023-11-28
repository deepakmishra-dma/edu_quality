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



def verify_invoice_portion(payment_schedule):
    total_portion = sum([ps.invoice_portion for ps in payment_schedule])
    if total_portion != 100:
        frappe.throw(title="Payment Schedule", msg="Total Invoice Portion must be 100%")

def verify_payment_term(payment_schedule):
    terms = []
    for ps in payment_schedule:
        if ps.payment_term in terms:
            frappe.throw(title="Payment Schedule", msg="Duplicate Terms not allowed")
        else:
            terms.append(ps.payment_term)


def before_update(doc,method=None):   
    if doc.parent_otp == 0:
        doc.need_otp = 1
        frappe.msgprint(title="Payment Schedule", msg="Please Verify parent OTP to Update Payment Schedule")
        return
    
    verify_invoice_portion(doc.payment_schedule)
    verify_payment_term(doc.payment_schedule)
    
    old_doc = doc.get_doc_before_save()
    if old_doc.payment_plan != doc.payment_plan:
        return
    elif old_doc.payment_schedule != doc.payment_schedule:
        for term,old_term in zip(doc.payment_schedule,old_doc.payment_schedule):
            if old_term.outstanding == 0 and term.outstanding != 0:
                frappe.throw("Cannot Change term - " + term.payment_term + " As it is already Paid!")
            if term.invoice_portion:
                term.payment_amount = (term.invoice_portion * doc.grand_total)/100
            elif term.payment_amount:
                term.invoice_portion = (term.payment_amount/doc.grand_total)*100

        payment_schedule = doc.payment_schedule
        doc.payment_schedule = []
        old_payment_plan = frappe.get_doc("Payment Plan", doc.payment_plan)

        for i, ps in enumerate(payment_schedule):
            amount = (ps.invoice_portion * doc.grand_total) / 100
            description = f"Installment {i+1}"
            deposit = get_deposit(old_doc.payment_schedule, old_payment_plan.payment_schedule)

            # if it is 1st term and deposit in previous payment schedule is not 0
            if i == 0 and deposit != 0:
                description += " and Deposit"
                amount += deposit

            doc.append("payment_schedule",{
                'payment_term':ps.payment_term,
                'description': description,
                'invoice_portion': ps.invoice_portion,
                'payment_amount':amount,
                'outstanding':amount,
                'due_date':ps.due_date
            })
        update_payment_request_after_discount(doc)

def get_deposit(doc_payment_plan, payment_plan):
    if "deposit" in doc_payment_plan[0].description.lower():
        return doc_payment_plan[0].payment_amount - payment_plan[0].payment_amount
    return 0

@frappe.whitelist()
def update_payment_plan(payment_plan, fee_name):
    doc = frappe.get_doc("Fees", fee_name)
    for ps in doc.payment_schedule:
        if ps.outstanding == 0:
            frappe.throw(f"Cannot Change Payment Plan As {ps.term} is already Paid!")

    old_payment_plan = frappe.get_doc("Payment Plan", doc.payment_plan)
    deposit = get_deposit(doc.payment_schedule, old_payment_plan.payment_schedule)
    payment_plan = frappe.get_doc("Payment Plan", payment_plan)
    doc.payment_schedule = []

    for i, ps in enumerate(payment_plan.payment_schedule):
        description = f"Installment {i+1}"
        amount = (ps.invoice_portion * doc.grand_total) / 100
        if i == 0 and deposit != 0:
            description += " and Deposit"
            amount += deposit
        doc.append("payment_schedule",{
            'payment_term':ps.payment_term,
            'description': description,
            'invoice_portion': ps.invoice_portion,
            'payment_amount':amount,
            'outstanding':amount,
            'due_date':ps.due_date
        })
    doc.payment_plan = payment_plan.name
    doc.save(ignore_permissions=True)
    frappe.response['message'] = "Payment Plan Updated Successfully!"


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
                "academic_year": student_applicant.academic_year,
                "custom_school": student_applicant.school,
                "company": student_applicant.institution
            })
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
            payment_entry(self,ref_doc,deposits,deposits,company.default_payable_account)
        if fees:
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


