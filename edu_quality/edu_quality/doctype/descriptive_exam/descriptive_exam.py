# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.public.py.utils import extract_year_from_academic_year_name
from frappe.model.mapper import get_mapped_doc


class DescriptiveExam(Document):
    def autoname(self, method=None):
        self.name = name_func(self)
        pass


@frappe.whitelist()
def name_func(descriptive_exam_doc):
    descriptive_exam_doc = (
        json.loads(descriptive_exam_doc)
        if isinstance(descriptive_exam_doc, str)
        else descriptive_exam_doc
    )
    division = frappe.get_doc(
        "Student Group", descriptive_exam_doc.get("student_group")
    )
    program = frappe.get_doc("Program", division.get("program"))

    academic_year = extract_year_from_academic_year_name(
        descriptive_exam_doc.get("academic_year") or current_academic_year()
    )

    class_type = program.get("program_name")

    class_type_doc = frappe.get_doc("Class Type", class_type)

    return f"{descriptive_exam_doc.name1} {class_type_doc.short_code}{division.get('student_group_name')} {academic_year}"


@frappe.whitelist()
def add_question(source_name, target_doc=None, ignore_permissions=False):
    # def postprocess(source, target):
    #     set_missing_values(source, target)
    #     # Get the advance paid Journal Entries in Sales Invoice Advance
    #     if target.get("allocate_advances_automatically"):
    #         target.set_advances()

    # def set_missing_values(source, target):
    #     target.flags.ignore_permissions = True
    #     target.run_method("set_missing_values")
    #     target.run_method("set_po_nos")
    #     target.run_method("calculate_taxes_and_totals")

    #     if source.company_address:
    #         target.update({"company_address": source.company_address})
    #     else:
    #         # set company address
    #         target.update(get_company_address(target.company))

    #     if target.company_address:
    #         target.update(
    #             get_fetch_values(
    #                 "Sales Invoice", "company_address", target.company_address
    #             )
    #         )

    #     # set the redeem loyalty points if provided via shopping cart
    #     if source.loyalty_points and source.order_type == "Shopping Cart":
    #         target.redeem_loyalty_points = 1

    #     target.debit_to = get_party_account("Customer", source.customer, source.company)

    doclist = get_mapped_doc(
        "Descriptive Question",
        source_name,
        {
            "Descriptive Question": {
                "doctype": "Descriptive Exam Question",
                "field_map": {
                    "question": "name",
                    "parent_question": "parent_question",
                },
            }
        },
        target_doc,
        ignore_permissions=ignore_permissions,
    )

    doc = get_mapped_doc(
        "Descriptive Question",  # Source doctype
        source_name,  # Source name (usually the ID of the source document)
        {
            "Descriptive Question": {  # Source doctype key
                "doctype": "Descriptive Exam",  # Target doctype
                "field_map": {"name": "question"},
                "add_if_empty": True,  # Create target doc if not exists
            },
            "Descriptive Question": {  # Source doctype item
                "name": "questions",
                "doctype": "Descriptive Exam Question",  # Target doctype item
                "field_map": {
                    "name": "question",
                },
                "add_if_empty": True,
            },
        },
        target_doc,  # Optional target doc
    )

    return doc
