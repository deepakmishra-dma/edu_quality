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


def transform_data(items):
    item_map = {}
    item_codes = [item.get("item_code") for item in items]
    # school_warehouses = [item.get("warehouse") for item in items]

    # school_data = frappe.db.get_list(
    #     "School",
    #     filters=[["warehouse", "in", school_warehouses]],
    #     fields=["name", "warehouse"],
    # )
    item_data = frappe.db.get_list(
        "Item",
        filters=[["item_code", "in", item_codes]],
        fields=["name", "custom_chapter", "custom_subject", "item_code"],
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

    frappe.errprint(item_map)
    transformed_items = [item_map.get(item) for item in item_map]
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
def generate_html_table(self):
    self = json.loads(self) if isinstance(self, str) else self
    self = transform_data(self.get("items"))

    all_schools = frappe.db.get_list("School", fields=["name"])
    # school_names = [name.get("name") for name in all_schools]
    columns = get_columns(all_schools)
    frappe.errprint(columns)
    frappe.errprint(self)
    # HTML = frappe.render_template(
    #     {"data": self, "school_names": school_names, "columns": columns}
    # )

    return all_schools, columns, self


# edu_quality.overrides_hooks.purchase_order.create_purchase_receipt
@frappe.whitelist()
def create_purchase_receipt(self, school="Walnut School at Shivane", selected_items=[]):
    self = json.loads(self) if isinstance(self, str) else self

    if not len(selected_items):
        frappe.throw("No items selected")

    warehouse_to_name_map = get_warehouse_to_school_map(self.get("items"))
    receipt = make_purchase_receipt(source_name=self.get("name"))
    filtered_items = list(
        filter(
            lambda item: warehouse_to_name_map.get(item.get("warehouse")) == school
            and item.item_code in selected_items,
            receipt.get("items"),
        )
    )
    if len(filtered_items) == 0:
        frappe.msgprint(
            f"Quantity is 0 for the selected {school}, Please create receipt for another one"
        )
        return
    receipt.items = filtered_items
    receipt.rounded_total = 0
    receipt.insert()
    return receipt
