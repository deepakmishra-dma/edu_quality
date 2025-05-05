import frappe
from datetime import datetime,timedelta
from edu_quality.public.py.walsh.admin import send_notification
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
import requests

import json


def cron():
    config = frappe.get_site_config()
    databases = config.get("databases")
    for database in databases:
        frappe.enqueue(
            "edu_quality.mysql.migrate_mysql",
            database=database,
            is_async=True,
            queue="long",
            enqueue_after_commit=True,
            at_front=True,
        )


def time_based():
    frappe.enqueue(
        "edu_quality.discount.time_based_discount",
        is_async=True,
        queue="long",
        timeout=1800,
    )


def create_payment_request_before_due_date():
    today = datetime.today().date()
    fee_schedules = frappe.get_all("Fee Schedule")
    for fee_schedule in fee_schedules:
        before_days = frappe.get_value("Fee Schedule",fee_schedule.name,"create_payment_request_before")
        fee_list = frappe.get_all("Fees",{'fee_schedule':fee_schedule.name,'workflow_state':'Approved'})
        for fee in fee_list:
            fee_doc = frappe.get_doc("Fees",fee.name)
            for schedule in fee_doc.payment_schedule:
                if (schedule.due_date - today).days == before_days:
                    frappe.enqueue(
                        "edu_quality.public.py.student.create_payment_request",
                        fee=fee_doc,
                        term = schedule.payment_term,
                        is_async=True,
                        queue="long",
                        timeout=1800,
                    )


def create_payment_request_before_due_date_fee_advance():
    today_date = frappe.utils.getdate(frappe.utils.today())
    fee_advance_docs = frappe.get_all("Fee Advance")
    for fee_advance in fee_advance_docs:
        fee_advance_doc = frappe.get_doc("Fee Advance",fee_advance.name)
        due_date = fee_advance_doc.due_date
        if (due_date - today_date).days < 30:
            schedule_payment_request(fee_advance_doc, fee_advance_doc.payment_term)


def schedule_payment_request(doc, payment_term):
    filters = {
        "reference_name": doc.name,
        "docstatus": 1,
    }
    if doc.docstatus != 1:
        return
    if not frappe.db.exists("Payment Request", filters):
        frappe.enqueue(
            "edu_quality.public.py.student.create_payment_request",
            fee=doc,
            term = payment_term,
            is_async=True,
            queue="long",
            timeout=1800,
        )


def update_academic_year():
    frappe.enqueue(
        "edu_quality.edu_quality.server_scripts.utils.update_academic_year",
    )
    
    
def get_student_ids_by_division(division):
    sql_query = """
        SELECT
            d.name AS id,
            stud.student AS student
        FROM
            `tabStudent Group` AS d
        INNER JOIN
            `tabStudent Group Student` AS stud
        ON
            stud.parent = d.name
        WHERE
            stud.active = 1
            AND d.name = %(division)s
    """
    student_list = frappe.db.sql(sql_query, {'division': division}, as_dict=True)
    
    if student_list:  # Check if student_list is not empty
        return [student.get('student') for student in student_list]
    
    return []


def get_datetime_range():
    # Get current date and time in IST
    current_time = frappe.utils.now_datetime()

    # Calculate last day 7 PM in IST
    last_day_7pm = (current_time.replace(hour=19, minute=0, second=0, microsecond=0) - timedelta(days=1)).replace(tzinfo=None)

    # Calculate today 7 PM in IST
    today_7pm = (current_time.replace(hour=19, minute=0, second=0, microsecond=0)).replace(tzinfo=None)

    return last_day_7pm, today_7pm

@frappe.whitelist()
def send_bulk_notification_cmap_to_guardian():
    current_academic_year = frappe.db.get_value('Academic Year',filters={'custom_current_academic_year': 1})
    last_day_7pm, today_7pm = get_datetime_range()
    print(last_day_7pm,today_7pm)
    sql_query = """
        SELECT
            cmapa.parent,
            cmapa.school,
            cmapa.division,
            cmapa.real_date,
            cmapa.teacher,
            cmap.academic_year,
            cmap.subject
        FROM
            `tabCMAP Assignment` cmapa
        INNER JOIN
            `tabCMAP` cmap
        ON
            cmap.name = cmapa.parent
        WHERE
            cmapa.real_date_updated_on BETWEEN %(last_day_7pm)s AND %(today_7pm)s
            AND cmap.academic_year = %(academic_year)s
    """
    cmaps_assignees = frappe.db.sql(sql_query,{ 'academic_year' : current_academic_year,'last_day_7pm':last_day_7pm,'today_7pm':today_7pm},as_dict=1)
    all_student_list = []
    for rec in cmaps_assignees:
        student_ids = get_student_ids_by_division(rec.get('division'))
        rec['student_ids'] = list(set(student_ids))
        all_student_list.extend(rec['student_ids'])
    notification_handler(list(set(all_student_list)))
 

def notification_handler(student_data):
    # for student in division_data.get('student_ids'):
    #     send_notification(student_id=student,subject="Time to check your curriculum updates! :)") 
    student_ids = tuple(student_data)
    if len(student_ids):
        guardian_details = frappe.db.sql(
            """SELECT gs.guardian as name, g.user
            FROM `tabStudent Guardian` gs
            INNER JOIN `tabGuardian` g ON g.name = gs.guardian
            WHERE gs.parent IN %(students)s """, 
            {'students': student_ids}, as_dict=1)
        print(guardian_details)
        
        final_guardian_list = {}
        
        if len(guardian_details) > 0:
            for i in guardian_details:
                if i.name not in final_guardian_list:
                    final_guardian_list[i.name] = i
                    
        if final_guardian_list:
            for guardian_name, guardian_data in final_guardian_list.items():
                send_notification_custom(subject="Time to check your curriculum updates! :)", guardian=guardian_data)


def send_notification_custom(subject, guardian):
    user = guardian.get("user")
    if user:
        push_tokens = frappe.get_all(
            "Mobile Push Token",
            filters={"user_id": user},
            fields=["token"]
        )
        for push_token in push_tokens:
            url = "https://exp.host/--/api/v2/push/send"               
            payload = json.dumps({
            "to": push_token.get("token"),
            "title": subject,
            "data": {"url_path": f"/cmap/"},
            # "body": json.dumps({"url_path": f"/notice/{notice_id}?student={student_id}"})
            })
            headers = {"Content-Type": "application/json"}
            requests.request("POST", url, headers=headers, data=payload)    

@frappe.whitelist()
def schedule_birthday_greeting(schedule_now=False):
    if not schedule_now and not frappe.db.get_single_value(
        "MGR Settings", "enable_birthday_greeting_scheduler"
    ):
        return None
    academic_year = current_academic_year()
    all_birthdays = frappe.db.sql(
        """
  SELECT * 
FROM `tabBirthday Card`
WHERE 
    MONTH(CONVERT_TZ(date_of_birth, 'UTC', 'Asia/Kolkata')) = MONTH(CONVERT_TZ(NOW(), 'UTC', 'Asia/Kolkata'))
    AND DAY(CONVERT_TZ(date_of_birth, 'UTC', 'Asia/Kolkata')) = DAY(CONVERT_TZ(NOW(), 'UTC', 'Asia/Kolkata')) AND academic_year = %(academic_year)s
""",
        as_dict=True,
        values={"academic_year":academic_year}
    )

    for birthday in all_birthdays:
        try:
            from nextai.funnel.custom_trigger import trigger_event

            birthday_doc = frappe.get_doc("Birthday Card", birthday)
            trigger_event(doc=birthday_doc, event_name="birthday_greeting")
        except Exception as e:
            frappe.logger("Birthday Card").exception(e)