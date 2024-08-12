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
    from_date = filters.get("from_date", "")
    to_date = filters.get("to_date", "")
    school = filters.get("school", ())
    program = filters.get("program", ())
    term = filters.get("term", "")
    student_status = filters.get("student_status", "")
    academic_year = filters.get("academic_year", "")

    sql_query = """
        SELECT 
            student.reference_number AS refno,
            CASE
                WHEN pr.reference_doctype = 'Fees' THEN f1.program
                WHEN pr.reference_doctype = 'Fee Advance' THEN f2.next_program
                ELSE NULL
            END AS program,
            COALESCE(f1.name, f2.name) AS fees,
            CONCAT_WS(" ", student.first_name, COALESCE(student.middle_name, ''), student.last_name) AS student,
            student.student_status AS student_status,
            COALESCE(f1.custom_school, f2.school) AS school,
            GROUP_CONCAT(DISTINCT fc.fees_category) AS fee_head_name,
            COALESCE(f1.payment_plan, f2.payment_plan) AS payment_plan,
            pr.payment_term AS payment_term,
            pr.grand_total AS amount_due,
            COALESCE(f1.academic_year, f2.academic_year) AS academic_year,
            student.joining_date AS admission_date, 
            COALESCE(f1.creation, f2.creation) AS creation_date,
            COALESCE(ps.due_date,  f2.due_date) AS due_date,
            student.student_email_id AS email_id, 
            student.student_mobile_number AS mobile_number, 
            COUNT(DISTINCT notification.name) AS notification_count

        FROM `tabPayment Request` AS pr        
        LEFT JOIN `tabFees` AS f1 ON pr.reference_doctype = 'Fees' AND f1.name = pr.reference_name
        LEFT JOIN `tabFee Advance` AS f2 ON pr.reference_doctype = 'Fee Advance' AND f2.name = pr.reference_name
        LEFT JOIN `tabStudent` AS student ON pr.party = student.name
        LEFT JOIN `tabPayment Schedule` AS ps ON COALESCE(f1.name, f2.name) = ps.parent AND pr.payment_term = ps.payment_term
        LEFT JOIN `tabNotification Log` AS notification ON pr.party = notification.student AND COALESCE(f1.program, f2.program) = notification.class AND COALESCE(f1.academic_year, f2.academic_year) = notification.academic_year AND pr.payment_term = notification.payment_term
        LEFT JOIN `tabFee Component` AS fc ON COALESCE(f1.name, f2.name) = fc.parent

        WHERE 
            pr.docstatus = 1
            AND pr.status != 'Paid'
            AND COALESCE(f1.docstatus, f2.docstatus) = 1
            AND COALESCE(ps.due_date,  f2.due_date) < CURDATE()
            {creation_condition}
            {school_condition}
            {class_condition}
            {term_condition}
            {s_s_condition}
            {academic_year_condition}
        GROUP BY 
            refno, program, fees, student, student_status, school, payment_plan, payment_term, amount_due, academic_year, admission_date, creation_date, due_date, email_id, mobile_number;
    """
    academic_year_condition = ""
    if academic_year:
        academic_year_condition  += " AND (COALESCE(f1.academic_year, f2.academic_year) =%(academic_year)s)"
    s_s_condition = ""
    if student_status:
        s_s_condition  += " AND student.student_status = %(student_status)s"
    term_condition = ""
    if term:
        term_condition  += " AND pr.payment_term = %(term)s"
    creation_condition = ""
    if from_date and to_date:
        creation_condition += " AND pr.creation BETWEEN %(from_date)s AND %(to_date)s"
    if from_date:
        creation_condition += " AND pr.creation >= %(from_date)s"
    if to_date:
        creation_condition += " AND pr.creation <= %(to_date)s"

    school_condition = ""
    if school:
        school_condition += " AND (f1.custom_school IS NULL OR f1.custom_school IN %(school)s) AND (f2.school IS NULL OR f2.school IN %(school)s)"
    class_condition = ""
    if program:
        class_condition += " AND (f1.program IS NULL OR f1.program IN %(program)s) AND (f2.next_program IS NULL OR f2.next_program IN %(program)s)"

    sql_query = sql_query.format(
        creation_condition=creation_condition,
        class_condition=class_condition,
        school_condition=school_condition,
        term_condition=term_condition,
        s_s_condition=s_s_condition,
        academic_year_condition=academic_year_condition
    )
    filter_data= {"from_date":from_date,
                  "to_date":to_date,
                  "school":tuple(school),
                  "program":tuple(program),
                  "term": term,
                  "student_status":student_status,
                  "academic_year":academic_year}
    frappe.logger("ssaaaaa").exception(filter_data)
    data = frappe.db.sql(sql_query, filter_data, as_dict=True)
    return data


@frappe.whitelist()
def send_payment_reminder(**kwargs):
    try:
        from nextai.funnel.custom_trigger import trigger_event
        kwargs['school'] = frappe.json.loads(kwargs.get('school'))
        kwargs['program'] = frappe.json.loads(kwargs.get('program'))
        data = get_data(kwargs)
        if not data:
            return "No data found"
        for row in data:
            payment_request = frappe.get_doc("Payment Request", {"reference_name": row[2]})
            trigger_event(doc=payment_request, event_name="payment_link_remainder")
        frappe.response["message"] = {
            "title": "Success",
            "msg": "Payment reminders sent successfully",
        }
    except ImportError:
        frappe.response["message"] = {
            "title": "Error",
            "msg": "Please install nextai app",
        }
    except Exception as e:
        frappe.logger("payment_reminder").exception(e)
        frappe.response["message"] = {
            "title": "Error",
            "msg": "Something went wrong",
        }

@frappe.whitelist()
def change_student_status(**kwargs):
    try:
        kwargs['school'] = frappe.json.loads(kwargs.get('school'))
        kwargs['program'] = frappe.json.loads(kwargs.get('program'))
        data = get_data(kwargs)
        if not data:
            return "No data found"
        for row in data:
            if row[0]:
                frappe.db.set_value("Student", {"reference_number":row[0]}, "student_status", "Defaulter")
        frappe.response["message"] = {
            "title": "Success",
            "msg": "Student Marked As Defaulter Successfully",
        }
    except Exception as e:
        frappe.logger("change_student_status").exception(e)
        frappe.response["message"] = {
            "title": "Error",
            "msg": "Something went wrong",
        }