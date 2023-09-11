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

def after_insert(doc,method=None):
    pe = frappe.get_doc("Program Enrollment", doc.program_enrollment)
    if pe.custom_payment_plan is not None:
        doc.payment_plan = pe.custom_payment_plan
    else:
        doc.payment_plan = frappe.db.get_value("Fee Schedule",doc.fee_schedule,'payment_plan')
    if doc.payment_plan:
                pp = frappe.get_doc("Payment Plan",doc.payment_plan)
                doc.payment_schedule = []
                initial_payment = 0
                for component in doc.components:
                    if component.fees_category in ["Deposit","deposit", "Application Fee","Application fee"]:
                        initial_payment = initial_payment +  component.amount
                i=0
                for schedule in pp.payment_schedule:
                    payment_amount = schedule.payment_amount
                    description = "Installment - " + str(i+1)
                    if i==0 and initial_payment>0:
                        before_days = frappe.db.get_value("Fee Schedule",doc.fee_schedule,"create_payment_request_before")
                        today = datetime.today().date()
                        difference = schedule.due_date - today
                        if difference.days > before_days:
                             frappe.logger("pr").exception("only deposit")
                             only_deposit(doc)
                        else:
                            payment_amount = payment_amount + initial_payment
                            description = description + " and deposit/application fee"
                            frappe.enqueue(
                                    "edu_quality.public.py.student.create_payment_request",
                                    fees=doc,
                                    term = schedule.payment_term,
                                    is_async=True,
                                    queue="long",
                                    timeout=1800,
                                )
                    i= i+1
                    doc.append("payment_schedule",{
                        'payment_term': schedule.payment_term,
                        'description': description,
                        'due_date': schedule.due_date,
                        'invoice_portion': schedule.invoice_portion,
                        'payment_amount': payment_amount,
                        'outstanding': payment_amount,
                    })

def before_save(doc,method=None):
    try:
        if not doc.get("school"):
            doc.school = frappe.db.get_value("Student",doc.student,"school")
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


def only_deposit(doc):    
        make_payment_request(
            party_type="Student",
            party=doc.student,
            dt="Fees",
            dn=doc.name,
            is_deposit=True,
            recipient_id=doc.student_email,
            submit_doc=True
        )

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


