import json

import frappe
from frappe.utils.data import flt

from edu_quality.public.py.utils import get_submitted_undertaking, get_undertaking_template


@frappe.whitelist()
def manual_payment(fee, term, data, payment_mode):
	from edu_quality.common.utils.access import assert_admin

	assert_admin()
	try:
		data = frappe.parse_json(data)
		if term == "Deposit":
			filters = [
				["Payment Request", "payment_term", "is", "not set"],
				["Payment Request", "reference_name", "=", fee],
				["Payment Request", "docstatus", "=", 1],
			]
		else:
			filters = {"reference_name": fee, "payment_term": term, "docstatus": 1}
		frappe.logger("man1").exception(filters)
		if frappe.db.exists("Payment Request", filters):
			frappe.enqueue(set_as_paid, queue="short", filters=filters, data=data, payment_mode=payment_mode)
			frappe.response["message"] = "Manual Payment Received Successfully"
			return
		frappe.response["message"] = "Error Occured"
	except Exception as e:
		frappe.logger("manual").exception(e)
		frappe.response["message"] = "Error Occured"
		return e


def set_as_paid(filters, data, payment_mode):
	frappe.db.set_value("Payment Request", filters, "mode_of_payment", payment_mode)
	pr = frappe.get_doc("Payment Request", filters)
	pr.save()
	pr.set_as_paid()
	entries = frappe.get_all(
		"Payment Entry", {"reference_no": pr.name}, ["name", "company", "party", "paid_amount"]
	)
	for entry in entries:
		for i in data:
			if entry.company == i.get("company"):
				reference_no = i.get("reference_number")
				update_reference(reference_no, entry, payment_mode)


def update_reference(reference_no, entry, payment_mode="Cash"):
	date = frappe.utils.nowdate()
	remarks = f"Amount INR {entry.paid_amount} received from {entry.party} Transaction reference no {reference_no} dated {date}"
	frappe.db.set_value("Payment Entry", entry.name, "reference_no", reference_no)
	frappe.db.set_value("Payment Entry", entry.name, "reference_date", date)
	frappe.db.set_value("Payment Entry", entry.name, "remarks", remarks)
	frappe.db.set_value("Payment Entry", entry.name, "mode_of_payment", payment_mode)


@frappe.whitelist()
def get_payment_details(fee, doctype, term):
	try:
		data = []
		company_wise = json.loads(frappe.db.get_value(doctype, fee, "company_split"))[term]
		for i in company_wise:
			data.append({"company": i, "amount": flt(company_wise[i]["amount"], 2), "reference": ""})
		return data
	except Exception as e:
		frappe.logger("manual").exception(e)


def company_wise(data, component):
	f = 0
	for i in data:
		if i.get("company") == component.get("company"):
			i["amount"] += component.get("amount")
			f = 1
			break
	if f == 0:
		data.append(component)
	return data


@frappe.whitelist()
def get_unpaid_terms(fee, doctype, payment_term=None):
	filters = [
		["reference_doctype", "=", doctype],
		["reference_name", "=", fee],
		["status", "!=", "Paid"],
		["docstatus", "=", 1],
	]
	terms = frappe.db.get_all("Payment Request", filters, "payment_term")
	result = []
	for term in terms:
		if not term.payment_term:
			result.append("Deposit")
		else:
			result.append(term.payment_term)
	fee_doc = frappe.get_doc(doctype, fee)
	is_deposit = False
	if fee_doc.component_split:
		component = json.loads(fee_doc.component_split).get("Term 1")
		is_deposit = component.get("is_deposit") if component else False
	if doctype == "Fees":
		school = fee_doc.custom_school
		filters = {"student": fee_doc.student, "program": fee_doc.program}
	else:
		school = fee_doc.school
		filters = {"student": fee_doc.student, "program": fee_doc.next_program}

	require_top = frappe.get_value("School", school, "custom_require_otp_for_accepting_rules_and_regulations")
	undertaking_enabled = bool(require_top)

	if require_top and frappe.get_value(
		"School", school, "custom_otp_for_every_installment_showing_rules_and_regulations"
	):
		filters["payment_term"] = payment_term

	if frappe.db.exists("Rules and Regulation Submission", filters, "name"):
		undertaking_accepted = True
	else:
		undertaking_accepted = False
	data = {
		"terms": result,
		"undertaking_accepted": undertaking_accepted,
		"undertaking_url": get_undertaking_template(is_deposit=is_deposit, fee=fee_doc),
		"undertaking_enabled": undertaking_enabled,
	}
	return data
