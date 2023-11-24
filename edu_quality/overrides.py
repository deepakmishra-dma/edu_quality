import frappe
from frappe import _
from frappe.utils import nowdate

from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_company_defaults,
)

from erpnext.accounts.doctype.payment_request.payment_request import PaymentRequest, _get_payment_gateway_controller, get_dummy_message, get_existing_payment_request_amount, get_gateway_details
from frappe.utils.data import flt


from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_company_defaults
)
from erpnext.accounts.party import get_party_bank_account
from edu_quality.public.py.utils import send_receipt_over_email

try:
    from nextai.funnel.custom_trigger import trigger_event
except ImportError:
    print("Chatnext is not installed")

class CustomPaymentRequest(PaymentRequest):
    def create_payment_entry(self):
        fee_doctype = self.reference_doctype
        fee_docname = self.reference_name
        fees = frappe.get_doc(fee_doctype, fee_docname)
        paid_from_dict = {}
        paid_to_dict = {}
        companies = {}
        fee_categories = {}
        for component in fees.components:
            fee_type = frappe.db.get_value("Fee Category",component.fees_category,"type")
            if not self.payment_term and fee_type != "Regular":
                continue
            doc = frappe.get_doc("Fee Category", component.fees_category)
            paid_to = doc.custom_account
            company = doc.custom_company
            paid_from = frappe.get_value(
                "Account", {"company": company, "account_type": "Receivable"}, ["name"]
            )
            amount = component.custom_amount_after_discount or component.amount
            if self.payment_term:
                is_deposit = False
                for schedule in fees.payment_schedule:
                    if schedule.payment_term == self.payment_term:
                        if "deposit" in schedule.description and fee_type != "Regular":
                            amount = flt(amount, 2)
                        elif fee_type == "Regular":
                            amount = flt((schedule.invoice_portion/100) * amount,2)
                        elif fee_type != "Regular":
                            is_deposit = True

                # flag for deposit, if it is not 1st term
                if is_deposit:
                    continue

                if paid_from_dict.get(paid_from) is not None:
                    paid_from_dict[paid_from] += amount
                    fee_categories[paid_from].append({component.fees_category:amount})
                else: 
                    paid_from_dict[paid_from] = amount
                    fee_categories[paid_from] = [{component.fees_category:amount}]
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
                fee_categories[paid_from]
            )
        if self.payment_term:
            mark_payment_term_paid(fees, self.payment_term, self.grand_total)
        paid_amount = fees.outstanding_amount - self.grand_total
        frappe.db.set_value(fees.doctype, fees.name, "outstanding_amount", paid_amount)
        self.db_set("status", "Paid")

        try:
            trigger_event(self, "deposit_paid_event")
        except Exception as e:
            frappe.logger('edu_quality').exception(e)

        send_receipt_over_email(self)

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
    

    def on_payment_authorized(self, status=None):
        if not status:
            return
        if status in ["Authorized", "Completed"]:
            self.set_as_paid()

    def on_submit(self):
        if self.payment_request_type == "Outward":
            self.db_set("status", "Initiated")
            return
        elif self.payment_request_type == "Inward":
            self.db_set("status", "Requested")

        if self.payment_channel != "Phone":
            self.set_payment_request_url()
            self.make_communication_entry()
            
        elif self.payment_channel == "Phone":
            self.request_phone_payment()


def payment_entry(doc, ref_doc, party_amount, paid_from, paid_to, company, cost_center, fee_categories=None):
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
            "payment_term": doc.payment_term,
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

    if fee_categories:
        for fee_category in fee_categories:
            for fee_name, amount in fee_category.items():
                payment_entry.append(
                    "fee_category",
                    {
                        "fee_category": fee_name,
                        "amount": amount,
                    },
                )

    payment_entry.insert(ignore_permissions=True)
    payment_entry.submit()
    return payment_entry

def get_amount(ref_doc, payment_account=None, is_deposit=False, payment_term=None):
    """get amount based on doctype"""
    dt = ref_doc.doctype
    if dt in ["Sales Order", "Purchase Order"]:
        grand_total = flt(ref_doc.rounded_total) or flt(ref_doc.grand_total)
    elif dt in ["Sales Invoice", "Purchase Invoice"]:
        if not ref_doc.get("is_pos"):
            if ref_doc.party_account_currency == ref_doc.currency:
                grand_total = flt(ref_doc.outstanding_amount)
            else:
                grand_total = flt(ref_doc.outstanding_amount) / ref_doc.conversion_rate
        elif dt == "Sales Invoice":
            for pay in ref_doc.payments:
                if pay.type == "Phone" and pay.account == payment_account:
                    grand_total = pay.amount
                    break
    elif dt == "POS Invoice":
        for pay in ref_doc.payments:
            if pay.type == "Phone" and pay.account == payment_account:
                grand_total = pay.amount
                break

    elif dt == "Fees" and is_deposit:
        grand_total = 0
        for f in ref_doc.components:
            fee_type = frappe.db.get_value("Fee Category",f.fees_category,"type")
            if fee_type and fee_type!= "Regular":
                grand_total += f.amount

    elif dt == "Fees" and payment_term:
        grand_total = 0
        for schedule in ref_doc.payment_schedule:
            if schedule.payment_term == payment_term:
                grand_total = frappe.db.get_value("Payment Schedule",schedule.name,"outstanding")

    elif dt == "Fees":
        grand_total = ref_doc.outstanding_amount

    if grand_total > 0:
        return grand_total
    else:
        frappe.throw(_("Payment Entry is already created"))

 
def create_fee_receipt(fees,payment_term=None, transaction_id=None):
    try:
        if not payment_term:
            categories = get_deposits(fees.components)
            due_date = nowdate()
        else:
            categories,due_date = get_categories(fees, payment_term)
        company_wise_split(fees, categories, due_date, payment_term, transaction_id)
    except Exception as e:
        frappe.logger('fee_receipt').exception(e)
        return e

def get_deposits(components):
    deposits = [component for component in components if component.fees_category in ["deposit", "Application fee"]]
    return deposits

def get_categories(fees,payment_term,due_date=nowdate(),description='description',invoice_portion=100):
    categories = []
    for schedule in fees.payment_schedule:
        if schedule.payment_term == payment_term:
            invoice_portion, due_date, description = schedule.invoice_portion, schedule.due_date, schedule.description
    for component in fees.components:
        if component.fees_category in ["deposit","Application fee"]:
            if 'deposit' in description:
                categories.append(component)
        else:
            component.amount = flt((invoice_portion/100) * component.amount,2)
            categories.append(component)
    return categories,due_date

def company_wise_split(fees, categories, due_date, payment_term=None, transaction_id=None):
    fee_categories = {}
    amounts = {}
    fee_amounts = {}

    for component in categories:
        fee_category = component.fees_category
        fee_amounts[fee_category] = component.amount
        company = frappe.get_value("Fee Category",fee_category, "custom_company")
        if fee_categories.get(company) is not None:
            fee_categories[company].append(fee_category)
            amounts[company] += component.amount
        else:
            fee_categories[company] = [fee_category]
            amounts[company] = component.amount

    for company, fee_categories in fee_categories.items():
            fee_receipt = frappe.new_doc("Fee Receipt")
            fee_receipt.fees = fees.name
            fee_receipt.due_date = due_date
            fee_receipt.company = company
            fee_receipt.paid_on = nowdate()
            fee_receipt.amount = amounts[company]
            fee_receipt.transaction_id = transaction_id
            fee_receipt.payment_term = payment_term
            fee_receipt.school = fees.custom_school

            for fee_category in fee_categories:
                fee_receipt.append("fee_category", {
                    "fee_category": fee_category,
                    "amount": fee_amounts[fee_category]
                })
            fee_receipt.insert(ignore_permissions=True)


def mark_payment_term_paid(fees, term, paid_amount):
    for schedule in fees.payment_schedule:
        if schedule.payment_term == term:
            if schedule.outstanding == paid_amount:
                frappe.db.set_value("Payment Schedule", schedule.name, "outstanding", 0)

@frappe.whitelist(allow_guest=True)
def make_payment_request(**args):
    """Make payment request"""

    args = frappe._dict(args)

    ref_doc = frappe.get_doc(args.dt, args.dn)
    gateway_account = get_gateway_details(args) or frappe._dict()
    frappe.logger('pr').exception(args.is_deposit)
    grand_total = get_amount(ref_doc, gateway_account.get("payment_account"), args.is_deposit, args.payment_term)
    frappe.logger('pr').exception(grand_total)
    if args.loyalty_points and args.dt == "Sales Order":
        from erpnext.accounts.doctype.loyalty_program.loyalty_program import validate_loyalty_points

        loyalty_amount = validate_loyalty_points(ref_doc, int(args.loyalty_points))
        frappe.db.set_value(
            "Sales Order", args.dn, "loyalty_points", int(args.loyalty_points), update_modified=False
        )
        frappe.db.set_value(
            "Sales Order", args.dn, "loyalty_amount", loyalty_amount, update_modified=False
        )
        grand_total = grand_total - loyalty_amount

    bank_account = (
        get_party_bank_account(args.get("party_type"), args.get("party"))
        if args.get("party_type")
        else ""
    )

    draft_payment_request = frappe.db.get_value(
        "Payment Request",
        {"reference_doctype": args.dt, "reference_name": args.dn, "docstatus": 0},
    )

    existing_payment_request_amount = get_existing_payment_request_amount(args.dt, args.dn)

    if existing_payment_request_amount:
        grand_total -= existing_payment_request_amount
    frappe.logger('pr').exception(grand_total)
    if draft_payment_request:
        frappe.db.set_value(
            "Payment Request", draft_payment_request, "grand_total", grand_total, update_modified=False
        )
        pr = frappe.get_doc("Payment Request", draft_payment_request)
    else:
        pr = frappe.new_doc("Payment Request")
        pr.update(
            {
                "payment_gateway_account": gateway_account.get("name"),
                "payment_gateway": gateway_account.get("payment_gateway"),
                "payment_account": gateway_account.get("payment_account"),
                "payment_channel": gateway_account.get("payment_channel"),
                "payment_request_type": args.get("payment_request_type"),
                "currency": "INR",
                "grand_total": grand_total,
                "mode_of_payment": args.mode_of_payment,
                "email_to": args.recipient_id or ref_doc.owner,
                "subject": _("Payment Request for {0}").format(args.dn),
                "message": gateway_account.get("message") or get_dummy_message(ref_doc),
                "reference_doctype": args.dt,
                "reference_name": args.dn,
                "party_type": args.get("party_type") or "Customer",
                "party": args.get("party") or ref_doc.get("customer"),
                "bank_account": bank_account,
            }
        )

        # Update dimensions
        pr.update(
            {
                "cost_center": ref_doc.get("cost_center"),
                "project": ref_doc.get("project"),
            }
        )

        for dimension in get_accounting_dimensions():
            pr.update({dimension: ref_doc.get(dimension)})

        if args.order_type == "Shopping Cart" or args.mute_email:
            pr.flags.mute_email = True

        pr.insert(ignore_permissions=True)
        if args.submit_doc:
            pr.submit()

    if args.order_type == "Shopping Cart":
        frappe.db.commit()
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = pr.get_payment_url()

    if args.return_doc:
        return pr

    return pr.as_dict()
