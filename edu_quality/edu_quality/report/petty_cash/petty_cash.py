# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.utils import get_balance_on


def execute(filters: dict | None = None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns() -> list[dict]:
    return [
        create_column("Timestamp", "timestamp", "Datetime", 180),
        create_column("Voucher No", "voucher_no", "Link", 200, "Journal Entry"),
        create_column("Company", "company", "Link", 300, "Company"),
        create_column("Category", "category", "Data", 100),
        create_column("School", "school", "Link", 200, "School"),
        create_column("Head Type", "head_type", "Link", 200, "Account"),
        create_column("Type", "type", "Data", 150),
        create_column("Amount", "amount", "Currency", 100),
        create_column("To/From", "to_from", "Data", 150),
        create_column("Created By", "created_by", "Link", 100, "User"),
        create_column("Voucher Status", "voucher_status", "Data", 150),
        create_column("Description", "description", "Data", 200),
    ]


def create_column(
    label: str, fieldname: str, fieldtype: str, width: int, options: str = None
) -> dict:
    column = {
        "label": _(label),
        "fieldname": fieldname,
        "fieldtype": fieldtype,
        "width": width,
    }
    if options:
        column["options"] = options
    return column


def get_data(filters) -> list[list]:
    base_filters = get_base_filters(filters)
    account = get_account(filters)
    journal_entries = fetch_journal_entries(base_filters)

    data = [prepare_data_entry(entry, filters.get("type")) for entry in journal_entries]

    if account:
        balance = get_balance_on(account, company=filters.get("company"))
        new_data = [""] * len(get_columns())
        new_data[0] = frappe.utils.now()
        new_data[2] = filters.get("company")
        new_data[6] = "Opening Amount"
        new_data[7] = balance
        if data:
            data.insert(0, new_data)

    return data


def get_base_filters(filters) -> dict:
    base_filters = {"docstatus": 1}

    if filters.get("company"):
        base_filters["company"] = filters["company"]

    if filters.get("school"):
        base_filters["user_remark"] = ["like", f"%{filters['school']}%"]

    if filters.get("type"):
        base_filters["voucher_type"] = (
            "Cash Entry" if filters["type"] == "Payment" else "Bank Entry"
        )
    if filters.get("date"):
        base_filters["posting_date"] = ["=", filters["date"]]

    return base_filters


def get_account(filters) -> str:
    if filters.get("school"):
        return frappe.get_value("School", filters["school"], "petty_cash_account")
    elif filters.get("company"):
        return frappe.get_value("Company", filters["company"], "default_petty_cash")
    return None


def fetch_journal_entries(base_filters) -> list:
    return frappe.get_all(
        "Journal Entry",
        fields=[
            "name",
            "voucher_type",
            "company",
            "owner",
            "user_remark",
            "total_debit",
            "pay_to_recd_from",
            "docstatus",
            "creation",
        ],
        filters=base_filters,
        order_by="posting_date desc",
    )


def prepare_data_entry(entry, _type) -> list:
    user_remark = frappe.parse_json(entry.user_remark or "{}")
    return [
        entry.creation,
        entry.name,
        entry.company,
        entry.voucher_type,
        user_remark.get("School"),
        frappe.get_value(
            "Journal Entry Account", {"parent": entry.name, "credit": 0}, "account"
        ),
        _type,
        entry.total_debit,
        entry.pay_to_recd_from,
        entry.owner,
        entry.docstatus,
        user_remark.get("Description"),
    ]
