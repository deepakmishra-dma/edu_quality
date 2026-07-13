import frappe
from frappe.utils import getdate, today

from edu_quality.public.py import discount as d


def time_based_discount():
	try:
		frappe.set_user("Administrator")
		if frappe.db.exists("Discount Configuration", {"type": "Time Based"}):
			docs = frappe.get_list("Discount Configuration", {"type": "Time Based"})
			for d in docs:
				dis = frappe.get_doc("Discount Configuration", d.name)
				if dis.start_date is not None and dis.end_date is not None:
					if dis.start_date <= getdate(today()) <= dis.end_date:
						fees = frappe.get_list("Fees", {"fee_structure": dis.fee_structure})
						for f in fees:
							fee = frappe.get_doc("Fees", f.name)
							apply_discount(fee)
					elif getdate(today()) > dis.end_date:
						fees = frappe.get_list("Fees", {"fee_structure": dis.fee_structure})
						for f in fees:
							fee = frappe.get_doc("Fees", f.name)
							remove_discount(fee)
	except Exception as e:
		frappe.logger("edu_quality").exception(e)


def apply_discount(doc):
	if doc.docstatus.is_cancelled():
		return
	for component in doc.components:
		if frappe.db.exists(
			"Discount Configuration",
			{
				"fee_structure": doc.fee_structure,
				"fee_category": component.fees_category,
				"type": "Time Based",
				"enabled": 1,
			},
		):
			dis = frappe.get_doc(
				"Discount Configuration",
				{
					"fee_structure": doc.fee_structure,
					"fee_category": component.fees_category,
					"type": "Time Based",
					"enabled": 1,
				},
			)
			d.add_discount(doc.name, dis.name)


def remove_discount(doc):
	if doc.docstatus.is_cancelled():
		return
	for component in doc.components:
		if frappe.db.exists(
			"Discount Configuration",
			{
				"fee_structure": doc.fee_structure,
				"fee_category": component.fees_category,
				"type": "Time Based",
				"enabled": 1,
			},
		):
			dis = frappe.get_doc(
				"Discount Configuration",
				{
					"fee_structure": doc.fee_structure,
					"fee_category": component.fees_category,
					"type": "Time Based",
					"enabled": 1,
				},
			)
			d.remove_discount(doc.name, dis.name)
