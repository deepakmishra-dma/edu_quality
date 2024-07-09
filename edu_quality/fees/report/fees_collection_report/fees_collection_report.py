import frappe


def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    columns = [
        {"label": "Ref No", "fieldname": "refno", "fieldtype": "Data", "width": 100},
        {
            "label": "Current Class",
            "fieldname": "program",
            "fieldtype": "Link",
            "options": "Program",
            "width": 150,
        },
        {
            "label": "Fees",
            "fieldname": "fees",
            "fieldtype": "Link",
            "options": "Fees",
            "width": 150,
        },
        {
            "label": "Student",
            "fieldname": "student",
            "fieldtype": "Link",
            "options": "Student",
            "width": 150,
        },
        {
            "label": "School",
            "fieldname": "school",
            "fieldtype": "Link",
            "options": "School",
            "width": 150,
        },
        {
            "label": "Cheque No",
            "fieldname": "cheque_no",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Payment Plan",
            "fieldname": "payment_plan",
            "fieldtype": "Link",
            "options": "Payment Plan",
            "width": 150,
        },
        {
            "label": "Payment Term",
            "fieldname": "payment_term",
            "fieldtype": "Link",
            "options": "Payment Term",
            "width": 150,
        },
        {
            "label": "Mode of Payment",
            "fieldname": "mode_of_payment",
            "fieldtype": "Link",
            "options": "Mode of Payment",
            "width": 150,
        },
        {
            "label": "Paid Amount",
            "fieldname": "paid_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "Transaction Date",
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": "Receipt ID",
            "fieldname": "receipt_id",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "width": 150,
        },
    ]
    return columns


def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    school = filters.get("school")
    doc_filter = {
        "docstatus": 1,
        # "posting_date": ["between", [from_date, to_date]],
        # "custom_school": school
    }
    fees = frappe.get_all(
        "Fees",
        doc_filter,
        [
            "name",
            "student",
            "custom_school",
            "program",
            "outstanding_amount",
            "payment_plan",
        ],
    )
    print(fees, filters)
    fee_data = []
    for fee in fees:
        refno = frappe.get_value("Student", fee.student, "reference_number")
        payment_entry = frappe.get_all(
            "Payment Entry",
            {"reference_name": fee.name},
            [
                "name",
                "reference_no",
                "posting_date",
                "paid_amount",
                "mode_of_payment",
                "payment_term",
            ],
        )
        if payment_entry:
            for payment in payment_entry:
                fee_data.append(
                    [
                        refno,
                        fee.program,
                        fee.name,
                        fee.student,
                        fee.custom_school,
                        payment.reference_no,
                        fee.payment_plan,
                        payment.payment_term,
                        payment.mode_of_payment,
                        payment.paid_amount,
                        payment.posting_date,
                        payment.name,
                    ]
                )
    return fee_data
