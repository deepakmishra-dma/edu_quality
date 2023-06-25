import frappe
from frappe import _
from frappe.utils import nowdate

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_company_defaults,
)
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest


class CustomPaymentRequest(PaymentRequest):
    def create_payment_entry(self):
        fee_doctype = self.reference_doctype
        fee_docname = self.reference_name
        fees = frappe.get_doc(fee_doctype, fee_docname)
        company = frappe.get_doc("Company", fees.company)
        sp = frappe.get_single("Split Payment")
        accounts = {i.fee_category: i.label.split()[0] for i in sp.easebuzz_accounts}
        labels = {i.label.split()[0]: i.account_name for i in sp.easebuzz_accounts}

        for component in fees.components:
            fee_name = component.fees_category
            label = accounts.get(fee_name)
            paid_to = labels.get(label) if labels.get(label) else sp.default_account
            company = frappe.get_value("Account", paid_to, ["company"])
            paid_from = frappe.get_value(
                "Account", {"company": company, "account_type": "Receivable"}, ["name"]
            )
            cost_center = frappe.get_value(
                "Cost Center", {"company": company}, ["name"]
            )
            payment_entry(
                self,
                fees,
                component.amount,
                paid_from,
                paid_to,
                company,
                cost_center,
            )
        for deposit in fees.deposits:
            paid_to = frappe.get_value(
                "Account", {"company": fees.company, "account_type": "Bank"}, ["name"]
            )
            paid_from = frappe.get_value(
                "Account",
                {"company": fees.company, "account_type": "Payable"},
                ["name"],
            )
            cost_center = frappe.get_value(
                "Cost Center", {"company": fees.company}, ["name"]
            )
            payment_entry(
                self,
                fees,
                deposit.amount,
                paid_from,
                paid_to,
                fees.company,
                cost_center,
            )

        frappe.db.set_value(fees.doctype, fees.name, "outstanding_amount", 0)


def payment_entry(doc, ref_doc, party_amount, paid_from, paid_to, company, cost_center):
    print(doc, ref_doc, party_amount, paid_from, paid_to, company, cost_center)
    frappe.set_user("Administrator")

    payment_entry = frappe.get_doc(
        {
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "company": company,
            "cost_center": cost_center,
            "posting_date": nowdate(),
            "reference_date": nowdate(),
            "mode_of_payment": doc.get("mode_of_payment"),
            "party_type": "Student",
            "party": ref_doc.student,
            "party_name": frappe.get_value("Student", ref_doc.student, "first_name"),
            "paid_from": paid_from,
            "paid_to": paid_to,
            "paid_amount": party_amount,
            "received_amount": party_amount,
            "source_exchange_rate": 1,
            "target_exchange_rate": 1,
        }
    )

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
            "cost_center": cost_center,
            "project": doc.get("project"),
        }
    )

    for dimension in get_accounting_dimensions():
        payment_entry.update({dimension: doc.get(dimension)})

    if payment_entry.difference_amount:
        company_details = get_company_defaults(company)

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
