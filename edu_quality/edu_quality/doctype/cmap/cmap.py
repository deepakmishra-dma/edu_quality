# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder.functions import Count, GROUP_CONCAT, Concat, Cast
from frappe.utils import parse_json
import json
from edu_quality.public.py.utils import check_admin_roles, to_snake_case
import string
import random
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
import frappe.utils
from frappe.query_builder import Order

# edu_quality.edu_quality.doctype.cmap.cmap


class CMAP(Document):
    def name_func(self):
        course_short_code = frappe.db.get_value(
            "Course", self.subject, "custom_short_code"
        )
        course_doc = frappe.get_doc("Course", self.subject)
        class_sortcode = frappe.db.get_value(
            "Class Type", self.get("class"), "short_code"
        )
        self.cmap_code = f"{self.academic_year}-{course_short_code}{class_sortcode}{self.unit}{self.period}"
        return self.cmap_code

    # def autoname(self, method=None):
    #     self.name_func()

    def before_save(self):
        self.name_func()
        if not self.is_new():
            doc_before_save = frappe.get_doc(self.doctype, self.name)
            for original_child in doc_before_save.table_vwbr:
                for child in self.table_vwbr:
                    if (
                        child.name == original_child.name
                        and child.real_date
                        and not original_child.get("real_date")
                    ):
                        child.real_date_updated_on = frappe.utils.now_datetime()
                        break
                    elif (
                        child.name == original_child.name
                        and original_child.get("real_date")
                        and child.real_date
                        and frappe.utils.getdate(child.real_date)
                        != frappe.utils.getdate(original_child.get("real_date"))
                    ):
                        child.real_date_updated_on = frappe.utils.now_datetime()
                        break

    def validate(self, method=None):
        fields = frappe.get_meta("Item Detail").fields
        mandatory = [i.get("fieldname") for i in fields if i.get("reqd") == 1]
        idx = 1
        for product in self.products:

            for mandate in mandatory:
                if product.get(mandate):
                    continue
                else:
                    frappe.throw(f"{mandate} is required for product at row {idx}")
            idx += 1

    def before_validate(self, method=None):
        if self.get("__islocal"):
            if self.reserved_for_portion_circular:
                insert_cmap_assignees(self)
            insert_cmap_instructor_assignees(self)

    def on_update(self, method=None):
        # old_doc = self.get_doc_before_save()
        # if old_doc and (
        #     self.reserved_for_portion_circular != old_doc.reserved_for_portion_circular
        #     or self.period != old_doc.period
        # ):
        #     self.name_func()
        pass


def insert_cmap_assignees(self):
    program_name = self.get("class")

    program_names = frappe.db.get_all("Program", filters={"program_name": program_name})
    program_list = [program.get("name") for program in program_names]

    divisions = frappe.db.get_all(
        "Student Group",
        filters={"academic_year": self.academic_year, "program": ["in", program_list]},
        fields=["name", "custom_school"],
    )
    for i in divisions:
        self.append(
            "table_vwbr",
            {
                "school": i.get("custom_school"),
                "division": i.get("name"),
            },
        )

        self.table_vwbr = get_unique_cmap_assignees(self.table_vwbr)


def insert_cmap_instructor_assignees(self):
    instructors = frappe.db.get_list(
        "Instructor Log",
        filters=[
            ["academic_year", "=", self.academic_year],
            ["program", "LIKE", f"{self.get('class')}-%"],
            ["course", "=", self.subject],
        ],
        fields=[
            "parent",
            "parent",
            "program",
            "student_group",
            "program",
            "program",
        ],
        ignore_permissions=True,
    )
    frappe.errprint(instructors)
    temp = []
    for i in instructors:
        self.append(
            "table_vwbr",
            {
                "school": "".join(i.get("program").split("-")[1::]),
                "teacher": i.get("parent"),
                "division": i.get("student_group"),
            },
        )

    self.table_vwbr = get_unique_cmap_assignees(self.table_vwbr)


def generate_text_from_unique_notes(self, type, added_broadcasts, field):
    if field is None:
        return
    if check_if_note_added_unique(type, added_broadcasts):

        setattr(
            self,
            field,
            "\\n".join([item or "" for item in added_broadcasts]),
        )


@frappe.whitelist()
def check_if_note_added_unique(material_type, added_items=[]):
    flag = True
    added_items = parse_json(added_items)
    frequency_counter = {}
    for item in added_items:
        frequency_counter[item] = (frequency_counter.get(item, 0) or 0) + 1

    index_dict = {}

    for description in added_items:
        if description in index_dict:
            index_dict[description].append(description)
        else:
            index_dict[description] = [description]

    for i in index_dict:
        for j in index_dict[i]:
            if frequency_counter.get(j) > 1:
                if i == None or not i:
                    continue
                flag = False
                frappe.msgprint(f"Description {i} or Doc is same for {material_type} ")

    return flag


def get_unique_cmap_assignees(data_list):
    unique_combinations = set()

    unique_items = []

    for item in data_list:
        combination = (item.get("school"), item.get("division"))

        if combination not in unique_combinations:
            unique_combinations.add(combination)
            unique_items.append(item)

    return unique_items


@frappe.whitelist(allow_guest=True)
def get_cmap_assignees_report(**filters):
    cmap_table = frappe.qb.DocType("CMAP")
    instructor_log_table = frappe.qb.DocType("Instructor Log")
    instructor_table = frappe.qb.DocType("Instructor")

    # cmap_assignment_table = frappe.qb.DocType("CMAP Assignment")
    # student_group_table = frappe.qb.DocType("Student Group")

    query = (
        frappe.qb.from_(cmap_table)
        .inner_join(instructor_log_table)
        .on((instructor_table.academic_year == cmap_table.academic_year))
        .select("*")
    )
    return query.run(as_dict=True)


@frappe.whitelist()
def get_cmap_period_no(self):
    self = json.loads(self) if isinstance(self, str) else self
    if not self.get("subject") or not self.get("academic_year"):
        return

    max_period_list = frappe.db.get_list(
        "CMAP",
        filters={
            "subject": self.get("subject"),
            "academic_year": self.get("academic_year"),
            "class": self.get("class"),
            "reserved_for_portion_circular": 0,
        },
        fields=["MAX(period)"],
    )

    max_period = max_period_list[0].get("MAX(period)", 0)
    if not self.get("period") and not max_period or isinstance(max_period, str):
        return 1
    elif str(self.get("period")) == max_period or not self.get("period"):
        return int(max_period) + 1


@frappe.whitelist()
def get_unique_material_query(filters):
    filters = json.loads(filters) if isinstance(filters, str) else filters
    materials = frappe.db.get_list(
        doctype="Item CMAP Material",
        filters=filters,
        ignore_permissions=True,
        fields=["name", "description"],
    )
    merged_array = []
    merged_dict = {}
    for key, value in materials:
        if value not in merged_dict:
            merged_dict[value] = key
            merged_array.append((key, value))

    return merged_array


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_current_and_next_year(doctype, txt, searchfield, start, page_len, filters):
    acad_year_table = frappe.qb.DocType("Academic Year")

    query = (
        frappe.qb.from_(acad_year_table)
        .where(
            (acad_year_table.custom_current_academic_year == 1)
            | (acad_year_table.custom_next_academic_year == 1)
        )
        .select(acad_year_table.name)
    )

    return query.run()


field_map = {
    "Material Required": "material_required",
    "Broadcast": "broadcast",
    "Home Work": "home_work",
    "Parent Note": "parent_note",
    "Class Work": "class_work",
}


def calculate_product_materials(name):
    cmap_doc = frappe.get_doc("CMAP", name)
    products = cmap_doc.get("products", [])
    product_names = [i.get("item") for i in products]
    item_table = frappe.qb.DocType("Item")
    material_table = frappe.qb.DocType("Item CMAP Material")

    # only return products having one material to minimize looping and updates
    query = (
        frappe.qb.from_(item_table)
        .inner_join(material_table)
        .on(material_table.parent == item_table.name)
        .where((item_table.name.isin(product_names)))
        .groupby(item_table.name, material_table.material_type)
        .having(Count(material_table.name) == 1)
        .select(
            material_table.name.as_("material_name"),
            item_table.name.as_("item_name"),
            material_table.material_type,
            material_table.description,
        )
    )
    data = query.run(as_dict=True)
    try:
        product_hash = {}
        for i in data:
            item = i.get("item_name")
            if item not in product_hash:
                product_hash[item] = [i]
            else:
                product_hash[item].append(i)

        for product in products:
            item = product.item
            if item in product_hash:
                for material in product_hash[item]:
                    frappe.db.set_value(
                        "Item Detail",
                        product.name,
                        field_map.get(material.get("material_type")),
                        material.get("description", ""),
                    )
    except Exception as e:
        frappe.log_error(
            f"Error while calculating Product Material for {name}",
            frappe.get_traceback(),
        )


# edu_quality.edu_quality.doctype.cmap.cmap.calculate_all_product_materials
@frappe.whitelist()
def calculate_all_product_materials():
    user_roles = frappe.get_roles(frappe.session.user)
    is_admin = check_admin_roles(user_roles, ["Content Admin", "Content Creator"])
    if not is_admin:
        frappe.throw(("User Is not allowed to run this method"))
    cmaps = frappe.get_all("CMAP")
    for i in cmaps:
        frappe.enqueue(calculate_product_materials, name=i.get("name"), queue="long")


# edu_quality.edu_quality.doctype.cmap.cmap.get_product_materials
@frappe.whitelist()
def get_product_materials(item_id):
    item_doc = frappe.get_doc("Item", item_id, ignore_permissions=True)
    result = {}

    for material in item_doc.custom_additional_material:
        material_type = material.get("material_type")
        description = material.get("description")
        if material_type not in result:
            result[material_type] = [None, description]
        # unique only
        elif result[material_type] and description not in result[material_type]:
            result[material_type].append(description)

    return result


@frappe.whitelist()
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


@frappe.whitelist()
def get_cmap_creation_headers():

    item_group_qb = frappe.qb.DocType("Item Group")

    item_group_query = (
        frappe.qb.from_(item_group_qb)
        .where((item_group_qb.parent_item_group == "CMAP"))
        .select(item_group_qb.name)
    )
    item_group_data = item_group_query.run(as_dict=True)

    item_group_headers = [
        {
            "fieldname": to_snake_case(group.get("name")),
            "label": group.get("name"),
            "type": "item_group",
        }
        for group in item_group_data
    ]
    meta = frappe.get_meta("CMAP")

    columns = [
        {"fieldname": "plan_date", "label": "Plan Date"},
        {"fieldname": "academic_year", "label": "Academic Year"},
        {"fieldname": "subject", "label": "Subject"},
        {"fieldname": "period", "label": "Period"},
        # {
        #     "fieldname": "reserved_for_portion_circular",
        #     "label": "Reserved For Portion Circular",
        # },
        {"fieldname": "class", "label": "Class"},
        {"fieldname": "unit", "label": "Unit"},
        {"fieldname": "last_period_of_the_unit", "label": "Last Period of the Unit"},
        {"fieldname": "textbook", "label": "Textbook"},
        {
            "fieldname": "chapter",
            "label": "Chapter",
        },
        {"fieldname": "broadcast", "label": "Broadcast"},
        {"fieldname": "parent_note", "label": "Parent Note"},
        {"fieldname": "home_work", "label": "Home Work"},
        {"fieldname": "class_work", "label": "Class Work"},
        {"fieldname": "material_required", "label": "Material Required"},
        *item_group_headers,
    ]
    return columns


@frappe.whitelist()
def get_cmap_list(academic_year, program, subject, unit, from_date=None, end_date=None):
    if not academic_year:
        academic_year = current_academic_year()
    acad_year_doc = frappe.get_doc("Academic Year", academic_year)

    if not from_date:
        from_date = acad_year_doc.year_start_date

    if not end_date:
        end_date = acad_year_doc.year_end_date
    cmap_qb = frappe.qb.DocType("CMAP")

    unit_cond = cmap_qb.unit.isin(unit or [None])

    if isinstance(unit, str):
        unit_cond = cmap_qb.unit == unit

    subject_cond = cmap_qb.subject.isin(subject or [None])

    if isinstance(subject, str):
        subject_cond = cmap_qb.subject == subject

    item_detail_qb = frappe.qb.DocType("Item Detail")
    cmap_assignment_qb = frappe.qb.DocType("CMAP Assignment")
    cmap_query = (
        frappe.qb.from_(cmap_qb)
        .inner_join(cmap_assignment_qb)
        .on(cmap_assignment_qb.parent == cmap_qb.name)
        .where(
            (cmap_qb.academic_year == academic_year)
            & (cmap_qb["class"] == program)
            & (cmap_qb.reserved_for_portion_circular == 0)
            & (unit_cond)
            & (subject_cond)
            # & ((cmap_qb.plan_date.isnull()) | (cmap_qb.plan_date[from_date:end_date]))
        )
        .groupby(cmap_qb.name)
        .select(
            cmap_qb.name,
            cmap_qb.academic_year,
            cmap_qb.plan_date,
            cmap_qb.unit,
            cmap_qb.subject,
            cmap_qb.period,
            cmap_qb["class"],
            cmap_qb.last_period_of_the_unit,
            # cmap_qb.reserved_for_portion_circular,
            # GROUP_CONCAT(cmap_assignment_qb.real_date).as_("real_dates"),
        )
    )

    final_query = (
        frappe.qb.from_(cmap_query)
        .inner_join(item_detail_qb)
        .on(
            (item_detail_qb.parent == cmap_query.name)
            & (item_detail_qb.parenttype == "CMAP")
        )
        .groupby(item_detail_qb.item_group, cmap_query.period)
        .orderby(Cast(cmap_query.period, "UNSIGNED"), Order.asc)
        .select(
            cmap_query.star,
            GROUP_CONCAT(item_detail_qb.item).as_("item_names"),
            item_detail_qb.item_group,
            GROUP_CONCAT(item_detail_qb.chapter).as_("chapter"),
            GROUP_CONCAT(item_detail_qb.textbook).as_("textbook"),
        )
    )

    return merge_different_item_group(final_query.run(as_dict=True))


def merge_different_item_group(data=[]):
    hashmap = {}
    for cmap in data:
        name = cmap.get("name")

        if name not in hashmap:
            hashmap[name] = cmap
            cmap[to_snake_case(cmap.item_group)] = cmap.item_names
            del cmap.item_names
            del cmap.item_group
        else:
            hashmap[name][to_snake_case(cmap.item_group)] = cmap.item_names
            del cmap.item_names
            del cmap.item_group
    return [value for key, value in hashmap.items()]


@frappe.whitelist()
def update_cmap(row):
    row = json.loads(row) if isinstance(row, str) else row

    if frappe.db.exists("CMAP", row.name):
        cmap_doc = frappe.get_doc("CMAP", row.name)

    else:
        pass


@frappe.whitelist()
def reorder_cmap_period(changed_cmaps):

    for cmap in changed_cmaps:
        name = cmap.get("name")
        new_period = cmap.get("new_period")

        cmap_doc = frappe.get_doc("CMAP", name)
        cmap_doc.period = new_period
        cmap_doc.name_func()
        cmap_doc.save()
    # ordered_cmaps = frappe.db.get_all(
    #     "CMAP",
    #     filters={
    #         "academic_year": academic_year,
    #         "class": class_type,
    #         "unit": unit,
    #         "subject": subject,
    #     },
    #     fields=["period", "name"],
    #     order_by="period",
    # )

    pass


# def add_cmap():
