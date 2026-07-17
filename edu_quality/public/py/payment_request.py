from datetime import datetime

import frappe

from edu_quality.overrides import make_payment_request


def before_save(doc, method=None):
	set_parent_email(doc)
	# if doc.reference_doctype == "Fees":
	#     # only deposit and application fee
	#     if not frappe.db.exists("Payment Request", {"reference_name": doc.reference_name}):
	#         fees = frappe.get_doc("Fees", doc.reference_name)
	#         if not doc.payment_term and doc.grand_total > 0:
	#             pass

	#     # if payment request has payment_term and reference_doctype is Fees
	#     if doc.payment_term and doc.reference_doctype == "Fees":
	#         fees = frappe.get_doc("Fees", doc.reference_name)
	#         previous_payment_term = get_previous_term(fees, doc.payment_term)
	#         # filter for not paid payment request
	#         not_paid_filter = {
	#             "reference_name": doc.reference_name,
	#             "status": ["!=", "Paid"],
	#         }
	#         # filter for paid payment request and previous payment term
	#         paid_filter = {
	#             "reference_name": doc.reference_name,
	#             "status": "Paid",
	#             "payment_term": previous_payment_term,
	#         }
	#         # if payment request is not paid
	#         # if frappe.db.exists("Payment Request", not_paid_filter):
	#         #     payment_request_not_paid(doc, fees, not_paid_filter)

	#         # if payment request is paid
	#         if frappe.db.exists("Payment Request", paid_filter):
	#             payment_request_paid(doc, fees, paid_filter, previous_payment_term)

	#         # if payment request does not exists
	#         else:
	#             create_pr_new_term(doc, fees)


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
	return None


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
	payment_amount = 0
	for schedule in fees.payment_schedule:
		if schedule.outstanding > 0:
			amount += frappe.utils.flt(schedule.payment_amount)
			today_date = frappe.utils.getdate(frappe.utils.today())
			if schedule.due_date < today_date and schedule.payment_term != doc.payment_term:
				frappe.db.set_value(
					"Payment Schedule", schedule.name, {"payment_amount": 0, "outstanding": 0}
				)
			elif schedule.payment_term == doc.payment_term:
				discount = get_discounted_amount(doc.payment_term, fees.outstanding_amount)
				payment_amount = amount - discount
				to_update = {
					"payment_amount": payment_amount,
					"outstanding": payment_amount,
					"discounted_amount": discount,
				}
				frappe.db.set_value("Payment Schedule", schedule.name, to_update)
	frappe.db.set_value("Fees", fees.name, "outstanding_amount", fees.outstanding_amount - discount)
	doc.grand_total = payment_amount


# if payment request is not paid
def payment_request_not_paid(doc, fees, not_paid_filter):
	pr = frappe.get_doc("Payment Request", not_paid_filter)
	if not pr.docstatus.is_cancelled() and not pr.docstatus.is_draft():
		amount = pr.grand_total
		pr.cancel()

		for schedule in fees.payment_schedule:
			if schedule.outstanding == 0:
				continue
			if schedule.payment_term == pr.payment_term:
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
				frappe.db.set_value("Payment Schedule", schedule.name, "outstanding", payment_amount)
				frappe.db.set_value("Payment Schedule", schedule.name, "discounted_amount", discount)
		frappe.db.set_value(
			"Fees",
			fees.name,
			"outstanding_amount",
			fees.outstanding_amount - discount,
		)
		doc.grand_total = payment_amount


# if payment request is paid
def payment_request_paid(doc, fees, paid_filter, previous_payment_term):
	pr = frappe.get_doc("Payment Request", paid_filter)
	# if previous payment term is discounted
	if not is_discounted(fees, previous_payment_term):
		for schedule in fees.payment_schedule:
			if schedule.outstanding == 0:
				continue
			if schedule.payment_term == doc.payment_term:
				amount = frappe.utils.flt(schedule.payment_amount)
				discount = get_discounted_amount(previous_payment_term, fees.outstanding_amount, True)
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
				frappe.db.set_value(
					"Fees",
					fees.name,
					"outstanding_amount",
					fees.outstanding_amount - discount,
				)
				doc.grand_total = payment_amount
	# if previous payment request is paid or previous payment term is discounted
	else:
		create_pr_new_term(doc, fees)


# update payment request after applying or removing discount
def update_payment_request_after_discount(doc):
	try:
		# filter for not paid payment request
		not_paid_filter = {
			"reference_name": doc.name,
			"status": ["=", "Initiated"],
			"payment_term": ["is", "set"],
		}
		# if payment request is not paid
		if frappe.db.exists("Payment Request", not_paid_filter):
			update_not_paid_payment_request(doc, not_paid_filter)
		if doc.doctype == "Fees":
			before_days = frappe.db.get_value(
				"Fee Schedule", doc.fee_schedule, "create_payment_request_before"
			)
			today = datetime.today().date()
			student_email = frappe.get_value("Student", doc.student, "student_email_id")
			for schedule in doc.payment_schedule:
				difference = schedule.due_date - today
				if difference.days <= before_days and not frappe.db.exists(
					"Payment Request", {"reference_name": doc.name, "payment_term": schedule.payment_term}
				):
					make_payment_request(
						party_type="Student",
						party=doc.student,
						dt=doc.doctype,
						dn=doc.name,
						payment_term=schedule.payment_term,
						recipient_id=student_email,
						submit_doc=True,
					)

	except Exception:
		frappe.log_error(title="Update Payment Request After Discount Error", message=frappe.get_traceback())


# create new payment request if previous payment request is not paid
def update_not_paid_payment_request(doc, not_paid_filter):
	pr = frappe.get_doc("Payment Request", not_paid_filter)
	if not pr.docstatus.is_cancelled() and not pr.docstatus.is_draft():
		pr.cancel()
		student_email = frappe.get_value("Student", doc.student, "student_email_id")
		make_payment_request(
			party_type="Student",
			party=doc.student,
			dt=doc.doctype,
			dn=doc.name,
			payment_term=pr.payment_term,
			recipient_id=student_email,
			submit_doc=True,
		)


def on_submit(doc, method):
	try:
		frappe.enqueue(email_trigger, pr=doc.name, queue="long")
	except Exception as e:
		frappe.log_error(title="PaymentLink Error", message=frappe.get_traceback())


def email_trigger(pr):
	import time

	from nextai.funnel.custom_trigger import trigger_event

	time.sleep(5)
	status = frappe.db.get_value("Payment Request", pr, "docstatus")
	if status == 1:
		doc = frappe.get_doc("Payment Request", pr)
		trigger_event(doc=doc, event_name="payment_link")


@frappe.whitelist()
def get_payment_plan_details(payment_request):
	payment_request = frappe.get_doc("Payment Request", payment_request)
	fees = frappe.get_doc(payment_request.reference_doctype, payment_request.reference_name)
	return fees.payment_plan


def set_parent_email(doc):
	mother = frappe.get_value("Student Guardian", {"parent": doc.party, "relation": "Mother"}, "guardian")
	father = frappe.get_value("Student Guardian", {"parent": doc.party, "relation": "Father"}, "guardian")
	if father:
		doc.email_to = frappe.get_value("Guardian", mother, "email_address")
	if mother:
		doc.email_to = frappe.get_value("Guardian", father, "email_address")
