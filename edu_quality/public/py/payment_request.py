import frappe


def before_save(doc, method=None):
    amount = 0

    # if payment request has payment_term and reference_doctype is Fees
    if doc.payment_term and doc.reference_doctype == "Fees":
        fees = frappe.get_doc("Fees", doc.reference_name)
        previous_payment_term = get_previous_term(fees, doc.payment_term)
        # filter for not paid payment request
        not_paid_filter = {
            "reference_name": doc.reference_name,
            "status": ["!=", "Paid"],
        }
        # filter for paid payment request and previous payment term
        paid_filter = {
            "reference_name": doc.reference_name,
            "status": "Paid",
            "payment_term": previous_payment_term,
        }
        # if payment request is not paid
        if frappe.db.exists("Payment Request", not_paid_filter):
            pr = frappe.get_doc("Payment Request", not_paid_filter)
            if not pr.docstatus.is_cancelled():
                amount = pr.grand_total
                pr.cancel()

            for schedule in fees.payment_schedule:
                if schedule.payment_term == pr.payment_term:
                    frappe.db.set_value(
                        "Payment Schedule", schedule.name, "payment_amount", 0
                    )
                    frappe.db.set_value(
                        "Payment Schedule", schedule.name, "outstanding", 0
                    )
                if schedule.payment_term == doc.payment_term:
                    amount = amount + frappe.utils.flt(schedule.payment_amount)
                    discount = get_discounted_amount(doc.payment_term, fees.outstanding_amount)
                    payment_amount = amount - discount
                    frappe.db.set_value(
                        "Payment Schedule",
                        schedule.name,
                        "payment_amount",
                        payment_amount,
                    )
                    frappe.db.set_value(
                        "Payment Schedule", schedule.name, "outstanding", payment_amount
                    )
                    frappe.db.set_value(
                        "Payment Schedule", schedule.name, "discounted_amount", discount
                    )
            frappe.db.set_value("Fees", fees.name, "outstanding_amount", fees.outstanding_amount - discount)
            doc.grand_total = payment_amount

        # if payment request is paid
        elif frappe.db.exists("Payment Request", paid_filter):
            pr = frappe.get_doc("Payment Request", paid_filter)
            # if previous payment term is discounted
            if not is_discounted(fees, previous_payment_term):
                for schedule in fees.payment_schedule:
                    if schedule.payment_term == doc.payment_term:
                        amount = frappe.utils.flt(schedule.payment_amount)
                        discount = get_discounted_amount(
                            previous_payment_term, fees.outstanding_amount, True
                        )
                        payment_amount = amount - discount
                        frappe.db.set_value(
                            "Payment Schedule",
                            schedule.name,
                            "payment_amount",
                            payment_amount,
                        )
                        frappe.db.set_value(
                            "Payment Schedule",
                            schedule.name,
                            "outstanding",
                            payment_amount,
                        )
                        frappe.db.set_value(
                            "Payment Schedule",
                            schedule.name,
                            "discounted_amount",
                            discount,
                        )
                        frappe.db.set_value("Fees", fees.name, "outstanding_amount", fees.outstanding_amount - discount)
                        doc.grand_total = payment_amount
            # if previous payment request is paid or previous payment term is discounted
            else:
                create_pr_new_term(doc, fees)

        # if payment request does not exists
        else:
            create_pr_new_term(doc, fees)


def get_discounted_amount(term, amount, previous_installment_paid=False):
    total_discount = 0
    filters = {
        "type": "Payment Plan",
        "payment_plan": term,
        "previous_installment_paid": previous_installment_paid,
    }
    if frappe.db.exists("Discount Configuration", filters):
        doc = frappe.get_doc("Discount Configuration", filters)
        if doc.discount:
            total_discount = (amount * doc.discount) / 100
        else:
            total_discount = doc.discount_amount if doc.discount_amount else 0
    return total_discount


def get_previous_term(fees, installment):
    installments = []
    index = 0
    if fees.payment_plan:
        for schedule in fees.payment_schedule:
            installments.append(schedule.payment_term)
        if installment in installments:
            index = installments.index(installment)
            if index > 0:
                index = index - 1
    return installments[index]


def is_discounted(fees, term):
    for schedule in fees.payment_schedule:
        if schedule.payment_term == term:
            if schedule.discounted_amount:
                return True
    return False


# Create Payment Request for new term
def create_pr_new_term(doc, fees):
    amount = 0
    discount = 0
    for schedule in fees.payment_schedule:
        if schedule.due_date < frappe.utils.getdate(frappe.utils.today()):
            amount = amount + frappe.utils.flt(schedule.payment_amount)
            frappe.db.set_value("Payment Schedule", schedule.name, "payment_amount", 0)
            frappe.db.set_value("Payment Schedule", schedule.name, "outstanding", 0)
        if schedule.payment_term == doc.payment_term:
            amount = amount + frappe.utils.flt(schedule.payment_amount)
            discount = get_discounted_amount(doc.payment_term, fees.outstanding_amount)
            payment_amount = amount - discount
            frappe.db.set_value(
                "Payment Schedule",
                schedule.name,
                "payment_amount",
                payment_amount,
            )
            frappe.db.set_value(
                "Payment Schedule", schedule.name, "outstanding", payment_amount
            )
            frappe.db.set_value(
                "Payment Schedule", schedule.name, "discounted_amount", discount
            )
    frappe.db.set_value("Fees", fees.name, "outstanding_amount", fees.outstanding_amount - discount)
    doc.grand_total = payment_amount
