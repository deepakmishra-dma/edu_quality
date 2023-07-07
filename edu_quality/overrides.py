import frappe
from frappe import _
from frappe.utils import nowdate

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_company_defaults,
)
from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest, _get_payment_gateway_controller
from frappe.utils.data import flt


class CustomPaymentRequest(PaymentRequest):
    def create_payment_entry(self):
        fee_doctype = self.reference_doctype
        fee_docname = self.reference_name
        fees = frappe.get_doc(fee_doctype, fee_docname)
        paid_from_dict = {}
        paid_to_dict = {}
        companies = {}
        for component in fees.components:
            fee_name = component.fees_category
            if frappe.db.exists("Security Deposit", fee_name):
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
                if self.payment_term == "Term 1":
                    payment_entry(
                        self,
                        fees,
                        component.amount,
                        paid_from,
                        paid_to,
                        fees.company,
                        cost_center,
                    )
            else:
                doc = frappe.get_doc("Split Payment", fee_name)
                paid_to = doc.account
                company = doc.company
                paid_from = frappe.get_value(
                    "Account", {"company": company, "account_type": "Receivable"}, ["name"]
                )
                
                amount = component.custom_amount_after_discount
                if self.payment_term:
                    for schedule in fees.payment_schedule:
                        if schedule.payment_term == self.payment_term:
                            amount = flt((schedule.invoice_portion/100) * amount,2)

                if paid_from_dict.get(paid_from) is not None:
                    paid_from_dict[paid_from] += amount
                else:
                    paid_from_dict[paid_from] = amount
                paid_to_dict[paid_from] = paid_to
                companies[paid_from] = company

        for paid_from, amount in paid_from_dict.items():
            cost_center = frappe.get_value(
                "Cost Center", {"company": companies[paid_from]}, ["name"]
            )
            payment_entry(
                self,
                fees,
                amount,
                paid_from,
                paid_to_dict[paid_from],
                companies[paid_from],
                cost_center,
            )
        
        frappe.db.set_value(fees.doctype, fees.name, "outstanding_amount", 0)
        self.db_set("status", "Paid")
        create_fee_receipt(fees,self.payment_term)

    def get_payment_url(self, **kwargs):
        if self.reference_doctype != "Fees":
            data = frappe.db.get_value(
				self.reference_doctype, self.reference_name, ["company", "customer_name"], as_dict=1
			)
        else:
            data = frappe.db.get_value(
				self.reference_doctype, self.reference_name, ["student_name"], as_dict=1
			)
            data.update({"company": frappe.defaults.get_defaults().company})
        controller = _get_payment_gateway_controller(self.payment_gateway)
        
        controller.validate_transaction_currency(self.currency)
        
        if hasattr(controller, "validate_minimum_transaction_amount"):
            controller.validate_minimum_transaction_amount(self.currency, self.grand_total)
            
        return controller.get_payment_url(
			**{
				"amount": flt(self.grand_total, self.precision("grand_total")),
				"title": data.company.encode("utf-8"),
				"description": self.subject.encode("utf-8"),
				"reference_doctype": "Payment Request",
				"reference_docname": self.name,
				"payer_email": self.email_to or frappe.session.user,
				"payer_name": frappe.safe_encode(data.customer_name),
				"order_id": self.name,
				"currency": self.currency,
                "payment_method": kwargs.get("payment_method")
			}
		)


def payment_entry(doc, ref_doc, party_amount, paid_from, paid_to, company, cost_center):
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


def create_fee_receipt(fees,payment_term=None):
    try:
        fee_categories = {}
        amounts = {}
        fee_amounts = {}
        for component in fees.components:
            amount = component.custom_amount_after_discount
            if payment_term:
                for schedule in fees.payment_schedule:
                    if schedule.payment_term == payment_term:
                        amount = flt((schedule.invoice_portion/100) * amount,2)
            fee_category = component.fees_category
            fee_amounts[fee_category] = amount
            company = frappe.get_value("Split Payment", {"fee_category":fee_category}, "company")
            if fee_categories.get(company) is not None:
                fee_categories[company].append(fee_category)
                amounts[company] += amount
            else:
                fee_categories[company] = [fee_category]
                amounts[company] = amount

        for company, fee_categories in fee_categories.items():
            fee_receipt = frappe.new_doc("Fee Receipt")
            fee_receipt.fees = fees.name
            fee_receipt.company = company
            fee_receipt.paid_on = nowdate()
            fee_receipt.amount = amounts[company]

            for fee_category in fee_categories:
                fee_receipt.append("fee_category", {
                    "fee_category": fee_category,
                    "amount": fee_amounts[fee_category]
                })
            fee_receipt.insert(ignore_permissions=True)
    except Exception as e:
        frappe.logger("edu_quality").exception(e)