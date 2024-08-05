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
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Student",
            "fieldname": "student",
            "fieldtype": "Data",
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

def get_payment_entries_and_append_fee_data(pe_filters, fee, student_name, refno, fee_data):
    fields = [
        "name",
        "reference_no",
        "reference_date",
        "paid_amount",
        "mode_of_payment",
        "payment_term",
    ]
    pe_filters["reference_name"] = fee.name
    payment_entries = frappe.get_all("Payment Entry", pe_filters, fields)
    for payment in payment_entries:
        fee_data.append(
            [
                refno,
                fee.program,
                fee.name,
                student_name,
                fee.custom_school,
                payment.reference_no,
                fee.payment_plan,
                payment.payment_term,
                payment.mode_of_payment,
                payment.paid_amount,
                payment.reference_date,
                payment.name,
            ]
        )

def get_data(filters):
    fee_filter = {"docstatus": 1}
    pe_filters = {"docstatus": 1}
    fee_advance_filter = {"docstatus": 1}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    school = filters.get("school")
    payment_mode = filters.get("payment_mode")

    if from_date:
        pe_filters["creation"] = [">=", from_date]
    if to_date:
        pe_filters["creation"] = ["<=", to_date]
    if payment_mode:
        pe_filters["mode_of_payment"] = payment_mode
    if school:
        fee_filter["custom_school"] = ["in", school]
        fee_advance_filter['school'] = ["in", school] 

    fee_data = []
    for fee_type, filters in [("Fees", fee_filter), ("Fee Advance", fee_advance_filter)]:
        fees = frappe.get_all(
            fee_type,
            filters,
            [
                "name",
                "student",
                "custom_school" if fee_type == "Fees" else "school",
                "program",
                "outstanding_amount",
                "payment_plan",
            ],
        )
        for fee in fees:
            refno = frappe.get_value("Student", fee.student, "reference_number")
            student_name = get_student_name(fee)
            get_payment_entries_and_append_fee_data(pe_filters, fee, student_name, refno, fee_data)

    return fee_data


def get_student_name(fee):
	student_name = frappe.get_value("Student", fee.student, ["first_name", "last_name"], as_dict=True)
	name = f"{student_name.first_name or ''} {student_name.last_name or ''}".strip()
	return name