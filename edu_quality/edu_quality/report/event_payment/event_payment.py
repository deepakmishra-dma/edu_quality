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
			"fieldname": "paid_date",
			"label": "Paid Date",
			"fieldtype": "Data",
			"width": 120,
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
			"fieldname": "payment_entry",
			"label": "Payment Entry",
			"fieldtype": "Link",
			"options": "Payment Entry",
			"width": 150,
		},
	]


def get_data(filters={}):
	event_detail = filters.get("event_detail")
	payment_status = filters.get("payment_status")

	conditions = ["ep.docstatus != 2"]

	if event_detail:
		conditions.append("ep.event_detail = %(event_detail)s")

	if payment_status:
		if payment_status == "Paid":
			conditions.append("ep.outstanding_amount = 0 OR pe.name IS NOT NULL")
		elif payment_status == "Unpaid":
			conditions.append("ep.outstanding_amount > 0")

	conditions_str = " AND ".join(conditions)
	filters["date_format"] = "%d-%m-%Y"

	query = f"""
        SELECT
            ep.name AS event_participant,
            ep.refno,
            ep.student_name AS student,
            ep.class,
            ep.division,
            ep.paid_amount,
            ep.outstanding_amount,
            COALESCE(pe.name, '') AS payment_entry,
            CASE
                WHEN ep.outstanding_amount > 0 THEN '<center>Unpaid</center>'
                ELSE CONCAT('<center>', DATE_FORMAT(pe.posting_date, %(date_format)s), '</center>')
            END AS paid_date
        FROM
            `tabEvent Participant` ep
        LEFT JOIN
            `tabPayment Entry` pe ON ep.name = pe.reference_name AND pe.docstatus = 1
        WHERE
            {conditions_str}
        GROUP BY
            ep.name, pe.posting_date
        ORDER BY
            pe.posting_date DESC
    """

	return frappe.db.sql(query, filters, as_dict=1)
