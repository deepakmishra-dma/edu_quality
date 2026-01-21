# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "fieldname": "refno",
            "label": "Refno",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "fieldname": "student",
            "label": "Student",
            "fieldtype": "Link",
            "options": "Student",
            "width": 200,
        },
        {
            "fieldname": "event_participant",
            "label": "Event Participant",
            "fieldtype": "Link",
            "options": "Event Participant",
            "width": 400,
        },
        {
            "fieldname": "class",
            "label": "Class",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "fieldname": "division",
            "label": "Division",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "fieldname": "payment_status",
            "label": "Payment Status",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "fieldname": "paid_amount",
            "label": "Paid Amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "fieldname": "outstanding_amount",
            "label": "Outstanding Amount",
            "fieldtype": "Currency",
            "width": 175,
        },
        {
            "fieldname": "payment_entry",
            "label": "Payment Entry",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 200,
        },
    ]


def get_data(filters):
    event_detail = filters.get("event_detail")
    participants = get_event_participants(event_detail)
    data = []
    for p in participants:
        payment_entry = frappe.get_value(
            "Payment Entry", filters={"reference_name": p.name}
        )

        data.append(
            {
                "refno": p.refno,
                "student": p.student_name,
                "event_participant": p.name,
                "payment_status": "Paid" if payment_entry else "Unpaid",
                "paid_amount": p.paid_amount,
                "outstanding_amount": p.outstanding_amount,
                "payment_entry": payment_entry,
                "class": p.get("class"),
                "division": p.division,
            }
        )

    payment_status = filters.get("payment_status")
    if payment_status:
        data = [d for d in data if d["payment_status"] == payment_status]

    return data


def get_event_participants(event_detail=None):
    fields = [
        "name",
        "paid_amount",
        "outstanding_amount",
        "student_name",
        "refno",
        "class",
        "division",
    ]
    event_filters = {}
    if event_detail:
        event_filters["event_detail"] = event_detail
    else:
        events = frappe.get_all(
            "Event Detail", {"web_form": ["is", "set"]}, pluck="name"
        )
        event_filters["event_detail"] = ["in", events]
    return frappe.get_all("Event Participant", event_filters, fields)
