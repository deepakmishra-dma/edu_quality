import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, cstr, flt, get_link_to_form


# edu_quality.api.scan_receipts.find_url_to_redirect_to
@frappe.whitelist()
def find_url_to_redirect_to(key):
    roles = frappe.get_roles()
    if (
        "Watchman" in roles
        and not "Administrator" in roles
        and not "System Manager" in roles
    ):
        if frappe.db.exists("Purchase Receipt", key):
            receipt_doc = frappe.get_doc("Purchase Receipt", key)
            receipt_doc.workflow_state = "Received"
            return receipt_doc.save(ignore_permissions=True)
    if frappe.db.exists("Purchase Order", key, cache=True):
        return f"/purchase-order/{key}"
    if frappe.db.exists("Purchase Receipt", key, cache=True):
        return f"/purchase-receipt/{key}"
    frappe.msgprint("Order and receipt with specified QR doesn't exist")
    return False


@frappe.whitelist()
def make_purchase_receipt(source_name, target_doc=None):
    def update_item(obj, target, source_parent):
        target.qty = flt(obj.qty) - flt(obj.received_qty)
        target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(
            obj.conversion_factor
        )
        target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
        target.base_amount = (
            (flt(obj.qty) - flt(obj.received_qty))
            * flt(obj.rate)
            * flt(source_parent.conversion_rate)
        )

    doc = get_mapped_doc(
        "Purchase Order",
        source_name,
        {
            "Purchase Order": {
                "doctype": "Purchase Receipt",
                "field_map": {"supplier_warehouse": "supplier_warehouse"},
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            "Purchase Order Item": {
                "doctype": "Purchase Receipt Item",
                "field_map": {
                    "name": "purchase_order_item",
                    "parent": "purchase_order",
                    "bom": "bom",
                    "material_request": "material_request",
                    "material_request_item": "material_request_item",
                    "sales_order": "sales_order",
                    "sales_order_item": "sales_order_item",
                    "wip_composite_asset": "wip_composite_asset",
                },
                "postprocess": update_item,
                "condition": lambda doc: abs(doc.received_qty) < abs(doc.qty)
                and doc.delivered_by_supplier != 1,
            },
            "Purchase Taxes and Charges": {
                "doctype": "Purchase Taxes and Charges",
                "add_if_empty": True,
            },
        },
        target_doc,
        set_missing_values,
    )

    return doc


def set_missing_values(source, target):
    target.run_method("set_missing_values")
    target.run_method("calculate_taxes_and_totals")
