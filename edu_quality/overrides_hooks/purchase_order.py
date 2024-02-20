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
                "field_name": item.get("item_code"),
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


@frappe.whitelist()
def generate_html_table(self):
    self = json.loads(self) if isinstance(self, str) else self
    self = transform_data(self.get("items"))

    all_schools = frappe.db.get_list("School", fields=["name"])
    school_names = [name.get("name") for name in all_schools]
    columns = ["Subject", "Chapter", "Code", *school_names, "Total Quantity"]
    template = """<table border="2" cellspacing="2">
  <thead>
    {% for column in columns %}
      <th>{{ column }}</th>
    {% endfor %}
  </thead>
  <tbody>
    {% for item in data %}
      <tr>
        <td>{{ item.get('subject') }}</td>
        <td>{{ item.get('chapter') }}</td>
        <td>{{ item.get('field_name') }}</td>
        {% for school_name in school_names %}
          <td>{{ item.get(school_name) }}</td>
        {% endfor %}
        <td>{{ item.get('total_qty') }}</td>
      </tr>
    {% endfor %}
  </tbody>
</table>"""

    template = """<div class="form-grid-container"><div class="form-grid" style="overflow-x: scroll;">
  <div class="grid-heading-row"><div class="grid-row"><div class="data-row row" style="flex-wrap:nowrap;">
    {% for column in columns %}
      <div class="col grid-static-col col-xs-2 static-area ellipsis"  title="{{column}}">{{ column }}</div>
    {% endfor %}
  </div></div></div>
  <div class="grid-body">
							<div class="rows">
    {% for item in data %}
      <div class="grid-row" data-name="cbbea21d3b" data-idx="1"><div class="data-row row" style="flex-wrap:nowrap;">
        <div class="col grid-static-col col-xs-2 bold" style="max-width:100%;">{{ item.get('subject') }}</div>
        <div class="col grid-static-col col-xs-2 bold" style="max-width:100%;">{{ item.get('chapter') }}</div>
        <div class="col grid-static-col col-xs-2 bold" style="max-width:100%;">{{ item.get('field_name') }}</div>
        {% for school_name in school_names %}
          <div class="col grid-static-col col-xs-2 bold" style="max-width:100%;">{{ item.get(school_name) }}</div>
        {% endfor %}
        <div class="col grid-static-col col-xs-2 bold" style="max-width:100%;">{{ item.get('total_qty') }}</div>
      </div></div>
    {% endfor %}
  </div></div>
</div>
</div>"""
    HTML = frappe.render_template(
        template, {"data": self, "school_names": school_names, "columns": columns}
    )

    return HTML, all_schools, columns, self


# edu_quality.overrides_hooks.purchase_order.create_purchase_receipt
@frappe.whitelist()
def create_purchase_receipt(self, school="Walnut School at Shivane"):
    self = json.loads(self) if isinstance(self, str) else self

    warehouse_to_name_map = get_warehouse_to_school_map(self.get("items"))
    receipt = make_purchase_receipt(source_name=self.get("name"))
    filtered_items = list(
        filter(
            lambda item: warehouse_to_name_map.get(item.get("warehouse")) == school,
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
