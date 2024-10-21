from edu_quality.public.py.utils import im_2_b64, gen_qr_code_b64
import frappe
import json
from frappe.model.mapper import get_mapped_doc
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
from datetime import datetime, date


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
    frappe.errprint(selected_items)
    item_data = frappe.db.get_list(
        "Item",
        filters=[["item_code", "in", item_codes]],
        fields=[
            "name",
            "custom_chapter",
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
                "chapter": item_code_data.get(item.get("item_code"), {}).get(
                    "custom_chapter"
                ),
                "subject": item_code_data.get(item.get("item_code"), {}).get(
                    "custom_subject"
                ),
                "product_url": item_code_data.get(item.get("item_code"), {}).get(
                    "custom_product_url"
                ),
                "receipt_created": (
                    purchase_receipt_items.get(item.get("item_code"))
                    if purchase_receipt_items
                    else False
                ),
                "printed": item.get("printed"),
                school_name: item.get("qty", 0),
                "total_qty": item.get("qty", 0),
            }
        else:
            last_qty_of_school = (
                item_map.get(item.get("item_code"), {}).get(school_name, 0) or 0
            )
            total_qty = item_map.get(item.get("item_code"), {}).get("total_qty", 0) or 0

            item_map[item.get("item_code")][school_name] = (
                last_qty_of_school + item.get("qty", 0)
            )

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
    calculate_print_count(self)


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
def get_linked_receipts(name, item_code):
    purchase_receipt_items = frappe.db.get_list(
        "Purchase Receipt Item",
        filters={"purchase_order": name, "item_code": item_code},
        fields=["name", "item_code", "parent"],
        ignore_permissions=True,
    )
    return purchase_receipt_items


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
        ignore_permissions=True,
    )
    frappe.errprint(purchase_receipt_items)
    if len(purchase_receipt_items):
        purchase_receipt_items = {
            i.get("item_code"): True for i in purchase_receipt_items
        }
    else:
        purchase_receipt_items = None
    self = transform_data(self.get("items"), selected_items, purchase_receipt_items)
    item_table = frappe.qb.DocType("Item")
    query = (
        frappe.qb.from_(item_table)
        .where((item_table.name.isin(selected_items or [None])))
        .select(item_table.custom_class)
    )
    all_classes = query.run(as_dict=True)
    classes_array = [i.get("custom_class") for i in all_classes]
    all_schools = frappe.db.get_list(
        "Program",
        fields=["school"],
        filters=[["program_name", "in", classes_array]],
        group_by="school",
    )
    schools_array = [i.get("school") for i in all_schools]

    school_docs = frappe.db.get_list("School", filters=[["name", "in", schools_array]])
    # school_names = [name.get("name") for name in all_schools]
    columns = get_columns(school_docs)

    return all_schools, columns, self


# edu_quality.overrides_hooks.purchase_order.create_purchase_receipt
@frappe.whitelist()
def create_purchase_receipt(self, school, selected_items=[]):
    self = json.loads(self) if isinstance(self, str) else self
    selected_items = (
        json.loads(selected_items)
        if isinstance(selected_items, str)
        else selected_items
    )
    # if not len(selected_items):
    #     frappe.throw("No items selected")
    school_prefix = frappe.db.get_value("School", school, "prefix")
    purchase_receipt_items = frappe.db.get_list(
        "Purchase Receipt Item",
        filters={"purchase_order": self.get("name")},
        fields=["name", "item_code", "warehouse"],
        ignore_permissions=True,
    )
    frappe.errprint("hh")
    frappe.errprint(selected_items)
    selected_item_map = get_selected_item_map(selected_items)
    warehouse_to_item_map = get_warehouse_to_item_map(purchase_receipt_items)
    warehouse_to_name_map = get_warehouse_to_school_map(self.get("items"))
    receipt = make_purchase_receipt(source_name=self.get("name"))
    frappe.errprint(selected_item_map)
    frappe.errprint(warehouse_to_item_map)
    frappe.errprint(warehouse_to_name_map)
    frappe.errprint(purchase_receipt_items)
    filtered_items = list(
        filter(
            lambda item: warehouse_to_name_map.get(item.get("warehouse")) == school
            and f"{item.get('item_code')}-{item.get('warehouse')}"
            not in warehouse_to_item_map
            and item.get("item_code") in selected_item_map,
            receipt.get("items"),
        )
    )
    frappe.errprint(filtered_items)
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


class SelfReturningDict(dict):
    def as_dict(self):
        return self


@frappe.whitelist()
# edu_quality.overrides_hooks.purchase_order.send_test_order_email
def send_test_order_email(self, user):
    try:

        self = json.loads(self) if isinstance(self, str) else self

        from nextai.funnel.custom_trigger import trigger_event

        if self.get("custom_is_cmap_print"):
            doc = frappe.get_doc("Purchase Order", self.get("name"))
            doc.custom_user_email = user
            doc.save(ignore_permissions=True)
            doc.reload()
            trigger_event(doc=doc, event_name="purchase_order")
            frappe.clear_messages()
        return "Success"
    except Exception as e:
        frappe.msgprint(str(e))


# marks item as printed


@frappe.whitelist()
def mark_item_as_printed(purchase_ord, item_code, checked):
    purchase_ord_doc = frappe.get_doc("Purchase Order", purchase_ord)
    count = 0
    for i in purchase_ord_doc.items:
        if i.get("item_code") == item_code:
            count += 1
            i.printed = 1 if checked == "true" else 0
            # frappe.db.set_value(
            #     "Purchase Order Item",
            #     i.get("name"),
            #     "printed",
            #     1 if checked == "true" else 0,
            # )
            # i["printed"] = checked
    if count == 0:
        return frappe.msgprint("Item not found in the current purchase order")
    calculate_print_count(purchase_ord_doc)
    purchase_ord_doc.save(ignore_permissions=True)
    purchase_ord_doc.reload()


def calculate_print_count(self):
    if not self.items:
        return 0
    self.custom_total_items = len(self.items)
    self.custom_printed_count = len([i for i in self.items if i.get("printed")])


@frappe.whitelist()
def convertyearMonthDate(date_input):

    if isinstance(date_input, date):
        date_str = date_input.strftime("%Y-%m-%d")
    else:
        date_str = date_input

    date_object = datetime.strptime(date_str, "%Y-%m-%d")

    formatted_date = date_object.strftime("%d-%m-%Y")
    return formatted_date
