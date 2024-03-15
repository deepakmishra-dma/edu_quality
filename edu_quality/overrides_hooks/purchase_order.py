from edu_quality.public.py.utils import im_2_b64, gen_qr_code_b64
import frappe
import json
from frappe.model.mapper import get_mapped_doc
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt


def get_warehouse_to_school_map(items):
    school_warehouses = [item.get("warehouse") for item in items]

    school_data = frappe.db.get_list(
        "School",
        filters=[["warehouse", "in", school_warehouses]],
        fields=["name", "warehouse"],
    )
    warehouse_to_name_map = {}
    for school in school_data:
        warehouse_to_name_map[school.get("warehouse")] = school.get("name")
    return warehouse_to_name_map


def get_warehouse_to_item_map(items):
    return {f"{item.get('item_code')}-{item.get('warehouse')}": True for item in items}


def get_selected_item_map(items):
    return {item: True for item in items}


def transform_data(items, selected_items, purchase_receipt_items=None):
    item_map = {}
    item_codes = [item.get("item_code") for item in items]

    item_data = frappe.db.get_list(
        "Item",
        filters=[["item_code", "in", item_codes]],
        fields=[
            "name",
            "custom_chapter",
            "custom_subject",
            "item_code",
            "custom_product_url",
        ],
    )
    item_code_data = {}
    warehouse_to_name_map = get_warehouse_to_school_map(items)
    for data in item_data:
        item_code_data[data.get("name")] = data

    for item in items:
        school_name = warehouse_to_name_map.get(item.get("warehouse")) or item.get(
            "warehouse"
        )
        if not item_map.get(item.get("item_code"), False):
            item_map[item.get("item_code")] = {
                "item_code": item.get("item_code"),
                "chapter": item_code_data.get(item.get("item_code"), {}).custom_chapter,
                "subject": item_code_data.get(item.get("item_code"), {}).custom_subject,
                "product_url": item_code_data.get(
                    item.get("item_code", {})
                ).custom_product_url,
                "receipt_created": purchase_receipt_items.get(item.get("item_code"))
                if purchase_receipt_items
                else False,
                school_name: item.get("qty", 0),
                "total_qty": item.get("qty", 0),
            }
        else:
            last_qty_of_school = (
                item_map.get(item.get("item_code"), {}).get(school_name, 0) or 0
            )
            total_qty = item_map.get(item.get("item_code"), {}).get("total_qty", 0) or 0

            item_map[item.get("item_code")][
                school_name
            ] = last_qty_of_school + item.get("qty", 0)

            item_map[item.get("item_code")]["total_qty"] = total_qty + item.get(
                "qty", 0
            )
    selected_items_hash = {}
    if selected_items:
        selected_items_hash = {i: True for i in selected_items}
    frappe.errprint(item_map)
    frappe.errprint(selected_items_hash)

    transformed_items = [
        item_map.get(item)
        for item in item_map
        if selected_items_hash.get(item) or selected_items == None
    ]
    frappe.errprint(transformed_items)
    return transformed_items


def before_validate(self, method=None):
    self.custom_qr_code_base = gen_qr_code_b64(self.name)


def get_columns(school_fields):
    school_array = []
    for i in school_fields:
        school_array.append(
            {
                "name": f"{i.get('name')}",
                "label": f"{i.get('name')}",
                "editable": False,
                "resizable": False,
                "sortable": False,
                "focusable": False,
                "dropdown": False,
                "width": 200,
            }
        ),
    columns = [
        {
            "name": "Subject",
            "id": "subject",
            "editable": False,
            "resizable": False,
            "sortable": False,
            "focusable": False,
            "dropdown": False,
            "width": 100,
        },
        {
            "name": "Chapter",
            "id": "chapter",
            "editable": False,
            "resizable": False,
            "sortable": False,
            "focusable": False,
            "dropdown": False,
            "width": 100,
        },
        {
            "name": "Code",
            "id": "item_code",
            "editable": False,
            "resizable": False,
            "sortable": False,
            "focusable": False,
            "dropdown": False,
            "width": 100,
        },
        {
            "name": "Total Quantity",
            "id": "total_qty",
            "editable": False,
            "resizable": False,
            "sortable": False,
            "focusable": False,
            "dropdown": False,
            "width": 100,
        },
        *school_array,
    ]
    return columns


@frappe.whitelist()
def generate_challan_list(self, selected_items=None):
    self = json.loads(self) if isinstance(self, str) else self
    selected_items = (
        json.loads(selected_items)
        if isinstance(selected_items, str)
        else selected_items
    )
    purchase_receipt_items = None
    # purchase_receipt_item_doc = frappe.qb.docType("Purchase Receipt Item")
    purchase_receipt_items = frappe.db.get_list(
        "Purchase Receipt Item",
        filters={"purchase_order": self.get("name")},
        fields=["name", "item_code"],
    )
    frappe.errprint(purchase_receipt_items)
    if len(purchase_receipt_items):
        purchase_receipt_items = {
            i.get("item_code"): True for i in purchase_receipt_items
        }
    else:
        purchase_receipt_items = None
    self = transform_data(self.get("items"), selected_items, purchase_receipt_items)

    all_schools = frappe.db.get_list("School", fields=["name"])
    # school_names = [name.get("name") for name in all_schools]
    columns = get_columns(all_schools)

    return all_schools, columns, self


# edu_quality.overrides_hooks.purchase_order.create_purchase_receipt
@frappe.whitelist()
def create_purchase_receipt(self, school, selected_items=[]):
    self = json.loads(self) if isinstance(self, str) else self

    # if not len(selected_items):
    #     frappe.throw("No items selected")
    school_prefix = frappe.db.get_value("School", school, "prefix")
    purchase_receipt_items = frappe.db.get_list(
        "Purchase Receipt Item",
        filters={"purchase_order": self.get("name")},
        fields=["name", "item_code", "warehouse"],
    )
    selected_item_map = get_selected_item_map(selected_items)
    warehouse_to_item_map = get_warehouse_to_item_map(purchase_receipt_items)
    warehouse_to_name_map = get_warehouse_to_school_map(self.get("items"))
    receipt = make_purchase_receipt(source_name=self.get("name"))
    filtered_items = list(
        filter(
            lambda item: warehouse_to_name_map.get(item.get("warehouse")) == school
            and f"{item.get('item_code')}-{item.get('warehouse')}"
            not in warehouse_to_item_map
            and item.get("item_code") in selected_item_map,
            receipt.get("items"),
        )
    )
    if len(filtered_items) == 0:
        frappe.msgprint(
            f"Quantity is 0 or receipt already created for the selected {school} and selected items, Please create receipt for another one"
        )
        return
    receipt.items = filtered_items
    receipt.rounded_total = 0
    frappe.errprint(receipt.as_dict())
    last = self.get("name").split("-")[-1]
    receipt.naming_series = f"MAT-PRE-.YYYY.-{last}-{school_prefix}-"
    receipt.insert()
    return receipt


@frappe.whitelist()
def create_purchase_receipt_for_all_schools(self, selected_items=None):
    schools = frappe.db.get_list("School")
    schools = [school.get("name") for school in schools]
    for school in schools:
        create_purchase_receipt(self, school, selected_items)
    return "Receipts Created Successfully"
