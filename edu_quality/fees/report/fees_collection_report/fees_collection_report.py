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

def get_data(filters):
    filter_data = {"docstatus": 1}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    school = filters.get("school")
    payment_mode = filters.get("payment_mode")

    if from_date:
        filter_data["from_date"] = from_date
    if to_date:
        filter_data["to_date"] = to_date
    if payment_mode:
        filter_data["mode_of_payment"] = payment_mode
    if school:
        filter_data["school"] = tuple(school)

    fee_data = []

    temp = """
           SELECT 
                s.reference_number as refno,
                COALESCE(f1.program, f2.next_program) AS program,
                COALESCE(f1.name, f2.name) AS fees,
                CONCAT_WS(" ", s.first_name, s.middle_name, s.last_name) AS student,
                COALESCE(f1.custom_school, f2.school) AS school,
                pe.reference_no as cheque_no,
                COALESCE(f1.payment_plan, f2.payment_plan) AS payment_plan,
                pe.payment_term,
                pe.mode_of_payment,
                pe.paid_amount,
                pe.reference_date as transaction_date,
                pe.name as receipt_id


        FROM `tabPayment Entry` pe
            LEFT JOIN `tabFees` AS f1 ON pe.reference_doctype = 'Fees' AND f1.name = pe.reference_name
            LEFT JOIN `tabFee Advance` AS f2 ON pe.reference_doctype = 'Fee Advance' AND f2.name = pe.reference_name
            LEFT JOIN `tabStudent` AS s ON s.name = COALESCE(f1.student, f2.student)
        WHERE 
           pe.docstatus = %(docstatus)s
            {creation_condition}
            {mode_of_payment_condition}
            {school_condition};
        """
    creation_condition = ""
    if from_date and to_date:
        creation_condition += " AND pe.reference_date BETWEEN %(from_date)s AND %(to_date)s"
    if from_date:
        creation_condition += " AND pe.reference_date >= %(from_date)s"
    if to_date:
        creation_condition += " AND pe.reference_date <= %(to_date)s"
    mode_of_payment_condition = ""
    if payment_mode:
        mode_of_payment_condition = " AND (pe.mode_of_payment IS NULL OR pe.mode_of_payment = %(mode_of_payment)s)"

    school_condition = ""
    if school:
        school_condition += " AND (f1.custom_school IS NULL OR f1.custom_school IN %(school)s) AND (f2.school IS NULL OR f2.school IN %(school)s)"

    # Replace placeholders in the query
    temp = temp.format(
        creation_condition=creation_condition,
        mode_of_payment_condition=mode_of_payment_condition,
        school_condition=school_condition
    )
    fee_data = frappe.db.sql(temp, filter_data, as_dict=True)
    return fee_data
