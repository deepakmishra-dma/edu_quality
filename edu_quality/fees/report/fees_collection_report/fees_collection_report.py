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


def get_data(filters):
    fee_filter = {"docstatus": 1}
    pe_filters = {"docstatus": 1,"status":"Paid"}
    fee_advacne_filter = {"docstatus": 1}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    school = filters.get("school")
    payment_mode = filters.get("payment_mode")

    if from_date and to_date:
        pe_filters["creation"] = ["between", [from_date, to_date]]
    if from_date:
        pe_filters["creation"] = [">=", from_date]
    if to_date:
        pe_filters["creation"] = ["<=", to_date]
    if payment_mode:
        pe_filters["mode_of_payment"] = payment_mode
    if school:
        fee_filter["custom_school"] = ["in", school]
        fee_advacne_filter['school'] = ["in", school] 

    fees = frappe.get_all(
        "Fees",
        fee_filter,
        [
            "name",
            "student",
            "custom_school",
            "program",
            "outstanding_amount",
            "payment_plan",
        ],
    )
    fee_data = []
    for fee in fees:
        refno = frappe.get_value("Student", fee.student, "reference_number")
        student_name = get_student_name(fee)
        pe_filters["reference_name"] =  fee.name
        payment_entry = frappe.get_all(
            "Payment Request",
            pe_filters,
            [
                "name",
                "party",
                "creation",
                "grand_total",
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
                        student_name,
                        fee.custom_school,
                        payment.party,
                        fee.payment_plan,
                        payment.payment_term,
                        payment.mode_of_payment,
                        payment.grand_total,
                        payment.creation,
                        payment.name,
                    ]
                )
    
    fee_advance = frappe.get_all(
        "Fee Advance",
        fee_advacne_filter,
        [
            "name",
            "student",
            "school",
            "program",
            "outstanding_amount",
            "payment_plan",
        ],
    )
    for fee in fee_advance:
        refno = frappe.get_value("Student", fee.student, "reference_number")
        student_name = get_student_name(fee)
        pe_filters["reference_name"] =  fee.name
        payment_entry = frappe.get_all(
            "Payment Request",
            pe_filters,
            [
                "name",
                "party",
                "creation",
                "grand_total",
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
                        student_name,
                        fee.school,
                        payment.party,
                        fee.payment_plan,
                        payment.payment_term,
                        payment.mode_of_payment,
                        payment.grand_total,
                        payment.creation,
                        payment.name,
                    ]
                )


    return fee_data


def get_student_name(fee):
	student_name = frappe.get_value("Student", fee.student, ["first_name", "last_name"], as_dict=True)
	name = f"{student_name.first_name or ''} {student_name.last_name or ''}".strip()
	return name