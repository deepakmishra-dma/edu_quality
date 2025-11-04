# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    deposit = get_data(filters)
    deposit_combined = get_data(filters, combined_deposit=True)
    data = deposit + deposit_combined
    return columns, data


def get_columns():
    columns = [
        {"label": "Ref No", "fieldname": "refno", "fieldtype": "Data", "width": 100},
        {
            "label": "Current Class",
            "fieldname": "program",
            "fieldtype": "Link",
            "options": "Program",
            "width": 250,
        },
        {
            "label": "Fees",
            "fieldname": "fees",
            "fieldtype": "Link",
            "options": "Fees",
            "width": 250,
        },
        {
            "label": "Student",
            "fieldname": "student",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Student Status",
            "fieldname": "student_status",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "School",
            "fieldname": "school",
            "fieldtype": "Link",
            "options": "School",
            "width": 200,
        },
        {
            "label": "Fee Head Name",
            "fieldname": "fee_head_name",
            "fieldtype": "Data",
            "width": 400,
        },
        {
            "label": "Payment Plan",
            "fieldname": "payment_plan",
            "fieldtype": "Link",
            "options": "Payment Plan",
            "width": 200,
        },
        {
            "label": "Payment Term",
            "fieldname": "payment_term",
            "fieldtype": "Link",
            "options": "Payment Term",
            "width": 150,
        },
        {
            "label": "Amount Due",
            "fieldname": "amount_due",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "Academic Year",
            "fieldname": "academic_year",
            "fieldtype": "Link",
            "options": "Academic Year",
            "width": 150,
        },
        {
            "label": "Admission Date",
            "fieldname": "admission_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": "Creation Date",
            "fieldname": "creation_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": "Email ID",
            "fieldname": "email_id",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": "Mobile Number",
            "fieldname": "mobile_number",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Notification Count",
            "fieldname": "notification_count",
            "fieldtype": "Int",
            "width": 150,
        },
    ]
    return columns


def get_data(filters, combined_deposit=False):
    from_date = filters.get("from_date", "")
    to_date = filters.get("to_date", "")
    school = filters.get("school", ())
    program = filters.get("program", ())
    student_status = filters.get("student_status", "")
    academic_year = filters.get("academic_year", "")

    sql_query = """
        SELECT 
            student.reference_number AS refno,
            fee.program AS program,
            fee.name AS fees,
            CONCAT_WS(" ", student.first_name, COALESCE(student.middle_name, ''), student.last_name) AS student,
            student.student_status AS student_status,
            fee.custom_school AS school,
            GROUP_CONCAT(
                DISTINCT CASE 
                WHEN fc.fees_category LIKE %(deposit)s
                THEN fc.fees_category ELSE NULL END
            ) AS fee_head_name,
            fee.payment_plan AS payment_plan,
            pr.payment_term AS payment_term,
            SUM(
                DISTINCT CASE 
                WHEN fc.fees_category LIKE %(deposit)s
                THEN fc.amount ELSE 0 END
            ) AS amount_due,
            fee.academic_year AS academic_year,
            student.joining_date AS admission_date, 
            fee.creation AS creation_date,
            student.student_email_id AS email_id, 
            student.student_mobile_number AS mobile_number, 
            COUNT(DISTINCT notification.name) AS notification_count

        FROM `tabPayment Request` AS pr        
        LEFT JOIN `tabFees` AS fee ON pr.reference_doctype = 'Fees' AND fee.name = pr.reference_name
        LEFT JOIN `tabStudent` AS student ON pr.party = student.name
        LEFT JOIN `tabNotification Log` AS notification ON pr.party = notification.student AND fee.program  = notification.class AND fee.academic_year = notification.academic_year
        LEFT JOIN `tabFee Component` AS fc ON fee.name = fc.parent
        """

    if combined_deposit:
        sql_query += """
            LEFT JOIN `tabPayment Schedule` as ps ON ps.parent = fee.name
            WHERE 
                pr.docstatus = 1
                AND fee.docstatus = 1
                AND pr.status = 'Paid'
                AND pr.payment_term = 'Term 1'
                AND ps.parenttype = 'Fees'
                AND ps.description LIKE %(deposit)s
                AND ps.outstanding = 0
        """
    else:
        sql_query += """
            WHERE 
                pr.docstatus = 1
                AND fee.docstatus = 1
                AND pr.status = 'Paid'
                AND pr.payment_term IS NULL
        """

    # these filters
    values = {
        "deposit": "%deposit%",
    }
    if from_date:
        sql_query += "AND (pr.creation >= %(from_date)s)"
        values["creation"] = from_date
    if to_date:
        sql_query += "AND (pr.creation <= %(to_date)s)"
        values["creation"] = to_date
    if school:
        sql_query += "AND (fee.custom_school IN %(school)s)"
        values["school"] = tuple(school)
    if program:
        sql_query += "AND (fee.program IN %(program)s)"
        values["program"] = tuple(program)
    if student_status:
        sql_query += "AND (student.student_status = %(student_status)s)"
        values["student_status"] = student_status
    if academic_year:
        sql_query += "AND (fee.academic_year = %(academic_year)s)"
        values["academic_year"] = academic_year

    sql_query += """
        GROUP BY
            refno, program, fees, student, student_status, school, payment_plan, payment_term, academic_year, admission_date, creation_date, email_id, mobile_number;
    """
    data = frappe.db.sql(sql_query, values, as_dict=True)
    return data
