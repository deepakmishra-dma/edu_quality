import frappe
from frappe import _
from frappe.utils import nowdate

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_company_defaults,
    get_payment_entry,
)
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest


class CustomPaymentRequest(PaymentRequest):
    def create_payment_entry(self, submit=True):
        """create entry"""
        frappe.flags.ignore_account_permission = True

        ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)

        if self.reference_doctype in ["Sales Invoice", "POS Invoice"]:
            party_account = ref_doc.debit_to
        elif self.reference_doctype == "Purchase Invoice":
            party_account = ref_doc.credit_to
        else:
            party_account = get_party_account(
                "Student", ref_doc.get("student"), ref_doc.company
            )

        party_account_currency = ref_doc.get(
            "party_account_currency"
        ) or get_account_currency(party_account)

        bank_amount = self.grand_total
        if (
            party_account_currency == ref_doc.company_currency
            and party_account_currency != self.currency
        ):
            party_amount = ref_doc.base_grand_total
        else:
            party_amount = self.grand_total

        payment_entry = get_payment_entry(
            self.reference_doctype,
            self.reference_name,
            party_amount=party_amount,
            bank_account=self.payment_account,
            bank_amount=bank_amount,
            party_type="Student",
            payment_type="Receive",
        )

        payment_entry.update(
            {
                "mode_of_payment": self.mode_of_payment,
                "reference_no": self.name,
                "reference_date": nowdate(),
                "remarks": "Payment Entry against {0} {1} via Payment Request {2}".format(
                    self.reference_doctype, self.reference_name, self.name
                ),
            }
        )

        # Update dimensions
        payment_entry.update(
            {
                "cost_center": self.get("cost_center"),
                "project": self.get("project"),
            }
        )

        for dimension in get_accounting_dimensions():
            payment_entry.update({dimension: self.get(dimension)})

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

        if submit:
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()

        return payment_entry



