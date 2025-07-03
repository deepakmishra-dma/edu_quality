# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from frappe.query_builder.functions import Count


class PermanentIdCard(Document):
    @frappe.whitelist()
    def create_order(self):
        academic_year = current_academic_year()
        permanent_id_card_doc = frappe.qb.DocType("Permanent Id Card")

        purchase_order = frappe.get_doc(
            {
                "doctype": "Purchase Order",
                "purpose": "Purchase",
                "items": [],
                "supplier": "Printer",
                "custom_academic_year": academic_year,
                "custom_is_id_card": 1,
                "custom_reference_doctype": "Permanent Id Card",
                "custom_reference_docname": self.name,
            }
        )

        if not frappe.db.exists("Item", "ID Card"):
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_name": "ID Card",
                    "item_code": "ID Card",
                    "custom_is_cmap": 0,
                }
            ).insert(ignore_permissions=True)

        bundled_items = bundle_all_cards(self)
        now_date = frappe.utils.nowdate()
        for item in bundled_items:

            purchase_order.append(
                "items",
                {
                    "item_code": "ID Card",
                    "qty": item.count,
                    "schedule_date": now_date,
                    "warehouse": item.warehouse,
                    "custom_sent_by": frappe.session.user,
                    "uom": "Nos",
                    "custom_print_file_url": self.file,
                    "school": item.school,
                },
            )

        if not len(bundled_items):
            frappe.throw("Can't Create Purchase Order without ID Cards")
        purchase_order = purchase_order.insert()
        frappe.get_doc(
            {
                "doctype": "Id Card Order",
                "parenttype": "Permanent Id Card",
                "parentfield": "orders",
                "parent": self.name,
                "purchase_order": purchase_order.name,
            }
        ).insert(ignore_permissions=True)

        return purchase_order


"""
Takes The doc and bundles all id card based on school
"""


def bundle_all_cards(doc):
    program_enrollment = frappe.qb.DocType("Program Enrollment")
    ind_perm_card_doc = frappe.qb.DocType("Individual Permanent Card")
    school_doc = frappe.qb.DocType("School")
    query = (
        frappe.qb.from_(ind_perm_card_doc)
        .inner_join(program_enrollment)
        .on(ind_perm_card_doc.program_enrollment == program_enrollment.name)
        .where(
            (ind_perm_card_doc.parent == doc.name)
            & (ind_perm_card_doc.parenttype == "Permanent ID Card")
        )
        .groupby(program_enrollment.custom_school)
        .select(program_enrollment.custom_school.as_("school"), Count("*").as_("count"))
    )
    final_query = (
        frappe.qb.from_(query)
        .inner_join(school_doc)
        .on(school_doc.name == query.school)
        .select(query.school, query.count, school_doc.warehouse)
    )

    return final_query.run(as_dict=True)


# edu_quality.fees.doctype.permanent_id_card.permanent_id_card.create_purchase_order
"""Create Purchase Orders for the specified permanent id card doc"""


@frappe.whitelist()
def create_purchase_order(name):
    try:
        if not frappe.db.exists("Permanent Id Card", name):
            frappe.throw(
                "Doesn't exist, the specified pdf for the name provided doesn't exist"
            )

        permanent_id_card = frappe.get_doc("Permanent Id Card", name)
        purchase_order = permanent_id_card.create_order()

        if purchase_order:
            return {
                "success": "Created Successfully",
                "name": purchase_order.get("name"),
            }

    except Exception as e:
        frappe.log_error(
            f"Error Creating Purchase Order for Permanent ID Card {name}",
            frappe.get_traceback(),
        )
        frappe.logger("Permanent ID Card").exception(e)
        frappe.throw(str(e))


# edu_quality.fees.doctype.permanent_id_card.permanent_id_card.mark_permanent_id_card_received
@frappe.whitelist()
def mark_permanent_id_card_received(id_cards, qr_scan=False):
    if not isinstance(id_cards, str):
        return
    list_of_cards = id_cards.split(",")
    for card in list_of_cards:
        if qr_scan:
            academic_year, school, ref_no = card.split("/")
            school_doc = frappe.get_doc("School", school)
            id_card_id = frappe.get_value(
                "Program Enrollment",
                filters={
                    "academic_year": academic_year,
                    "student": f"{school_doc.get('prefix','')}{ref_no}",
                },
                fieldname="custom_id_Card",
            )
        else:
            academic_year = current_academic_year()
            id_card_id = frappe.get_value(
                "Program Enrollment",
                filters={
                    "academic_year": academic_year,
                    "student": card,
                },
                fieldname="custom_id_Card",
            )
        id_card = frappe.db.get_doc("Student ID Card", id_card_id)
        id_card.status = "RECEIVED BY STUDENT"
        id_card.save(ignore_permissions=True)
