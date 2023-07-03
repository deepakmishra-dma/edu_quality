import frappe
from frappe.utils import today, getdate


def time_based_discount():
    try:
        frappe.set_user("Administrator")
        if frappe.db.exists("Discount Configuration", {"type": "Time Based"}):
            docs = frappe.get_list("Discount Configuration", {"type": "Time Based"})
            for d in docs:
                dis = frappe.get_doc("Discount Configuration", d.name)
                if dis.start_date is not None and dis.end_date is not None:
                    if dis.start_date <= getdate(today()) <= dis.end_date:
                        fees = frappe.get_list(
                            "Fees", {"fee_structure": dis.fee_structure}
                        )
                        for f in fees:
                            fee = frappe.get_doc("Fees", f.name)
                            apply_discount(fee)
                    elif getdate(today()) > dis.end_date:
                        fees = frappe.get_list(
                            "Fees", {"fee_structure": dis.fee_structure}
                        )
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
            frappe.db.set_value("Fee Component", component.name, "custom_discount", dis.name)
            frappe.db.set_value("Fee Component", component.name, "custom_discount_percentage", dis.discount)
            discounted_amount = (component.amount * float(dis.discount)) / 100
            frappe.db.set_value("Fee Component", component.name, "custom_discount_amount", discounted_amount)
            frappe.db.set_value("Fee Component", component.name, "custom_amount_after_discount", (component.amount - discounted_amount))
            grand_total = doc.grand_total - discounted_amount
            frappe.db.set_value("Fees", doc.name, "grand_total", grand_total)

    grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
    frappe.db.set_value("Fees", doc.name, "grand_total_in_words", grand_total_in_words)
    frappe.db.set_value("Fees", doc.name, "outstanding_amount", grand_total)


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
            frappe.db.set_value("Fee Component", component.name, "custom_discount", None)
            frappe.db.set_value("Fee Component", component.name, "custom_discount_percentage", 0)
            discounted_amount = component.custom_discount_amount
            frappe.db.set_value("Fee Component", component.name, "custom_discount_amount", 0)
            frappe.db.set_value("Fee Component", component.name, "custom_amount_after_discount", component.amount)
            grand_total = doc.grand_total + discounted_amount
            frappe.db.set_value("Fees", doc.name, "grand_total", grand_total)

    grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
    frappe.db.set_value("Fees", doc.name, "grand_total_in_words", grand_total_in_words)
    frappe.db.set_value("Fees", doc.name, "outstanding_amount", grand_total)
