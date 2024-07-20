import frappe
from frappe.utils.data import getdate, nowdate


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
            "width": 200,
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
            "width": 100,
        },
        {
            "label": "Amount Due",
            "fieldname": "amount_due",
            "fieldtype": "Currency",
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
            "label": "Due Date",
            "fieldname": "due_date",
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
    ]
    return columns


def get_data(filters):
    fee_filter = {"docstatus": 1}
    pr_filters = {"docstatus": 1, "status": ["!=", "Paid"]}
    fee_advance_filter = {"docstatus": 1}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    school = filters.get("school")

    if from_date and to_date:
        pr_filters["creation"] = ["between", [from_date, to_date]]
    if from_date:
        pr_filters["creation"] = [">=", from_date]
    if to_date:
        pr_filters["creation"] = ["<=", to_date]
    if school:
        fee_filter["custom_school"] = ["in", school]
        fee_advance_filter["school"] = ["in", school]

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
        admission_date = frappe.get_value("Student", fee.student, "joining_date")
        email = frappe.get_value("Student", fee.student, "student_email_id")
        mobile = frappe.get_value("Student", fee.student, "student_mobile_number")
        student_name = get_student_name(fee)
        fee_head_name = get_fee_heads(fee)
        pr_filters["reference_name"] = fee.name
        payment_request = frappe.get_all(
            "Payment Request",
            pr_filters,
            [
                "name",
                "creation",
                "grand_total",
                "payment_term",
            ],
        )
        if payment_request:
            for payment in payment_request:
                payment_term = "Deposit" if not payment.term else payment.term
                due_date = frappe.get_value(
                    "Payment Schedule",
                    {"parent": fee.name, "payment_term": payment_term},
                    "due_date",
                )
                if due_date and due_date < getdate(nowdate()):
                    fee_data.append(
                        [
                            refno,
                            fee.program,
                            fee.name,
                            student_name,
                            fee.custom_school,
                            fee_head_name,
                            fee.payment_plan,
                            payment_term,
                            payment.grand_total,
                            admission_date,
                            payment.creation,
                            due_date,
                            email,
                            mobile,
                        ]
                    )

    fee_advance = frappe.get_all(
        "Fee Advance",
        fee_advance_filter,
        [
            "name",
            "student",
            "school",
            "program",
            "outstanding_amount",
            "payment_plan",
            "due_date",
        ],
    )
    for fee in fee_advance:
        refno = frappe.get_value("Student", fee.student, "reference_number")
        admission_date = frappe.get_value("Student", fee.student, "joining_date")
        email = frappe.get_value("Student", fee.student, "student_email_id")
        mobile = frappe.get_value("Student", fee.student, "student_mobile_number")
        fee_head_name = get_fee_heads(fee)
        student_name = get_student_name(fee)
        pr_filters["reference_name"] = fee.name
        payment_request = frappe.get_value(
            "Payment Request",
            pr_filters,
            [
                "name",
                "creation",
                "grand_total",
                "payment_term",
            ],
            as_dict=True,
        )
        if payment_request:
            if fee.due_date < getdate(nowdate()):
                fee_data.append(
                    [
                        refno,
                        fee.program,
                        fee.name,
                        student_name,
                        fee.school,
                        fee_head_name,
                        fee.payment_plan,
                        payment_request.payment_term,
                        payment_request.grand_total,
                        admission_date,
                        payment_request.creation,
                        fee.due_date,
                        email,
                        mobile,
                    ]
                )

    return fee_data


def get_fee_heads(fees):
    components = frappe.get_all(
        "Fee Component",
        {"parent": fees.name},
        ["fees_category"],
    )
    fee_head_names = [component.fees_category for component in components]
    return ", ".join(fee_head_names)

def get_student_name(fee):
	student_name = frappe.get_value("Student", fee.student, ["first_name", "last_name"], as_dict=True)
	name = f"{student_name.first_name or ''} {student_name.last_name or ''}".strip()
	return name