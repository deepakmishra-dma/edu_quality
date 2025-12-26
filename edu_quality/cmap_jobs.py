import frappe
from frappe.utils.data import *
from frappe.utils import get_datetime, now_datetime, add_to_date

import datetime
import requests
import json
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


def generate_mention_html(base_url, user_id, message, name):
    mention_html = f'<div class="ql-editor read-mode"><p>'
    mention_html += (
        f'<span class="mention" data-id="{user_id}" '
        f'data-value="<a href=&quot;{base_url}/app/user-profile/{user_id}&quot; '
        f'target=&quot;_blank&quot;>{user_id}" '
        f'data-denotation-char="@" data-is-group="false" '
        f'data-link="{base_url}/app/user-profile/{user_id}">﻿'
        f'<span contenteditable="false"><span class="ql-mention-denotation-char">@</span>'
        f'<a href="{base_url}/app/user-profile/{user_id}" target="_blank">{name}</a>'
        f"</span>﻿</span> {message}</p></div>"
    )
    return mention_html


def add_mentions(comment_by, user_id, content, reference_doctype, reference_name, name):
    # Format the content to include mentions
    mentioned_html = ""
    mentioned_html += generate_mention_html(
        frappe.utils.get_url(), user_id, message=content, name=name
    )
    # Create a new comment document
    comment = frappe.get_doc(
        {
            "doctype": "Comment",
            "comment_type": "Comment",
            "comment_by": comment_by,
            "content": f"{mentioned_html}",
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
        }
    )

    # Save the comment
    comment.insert(ignore_permissions=True)


def test():
    comment_by = "chanchal@walnutedu.in"
    mentioned_users = "chanchal@walnutedu.in"
    name = "Chanchal Kulkarni"
    content = "Your Next PTM Meeting for Class Division 10A and Subject "
    reference_doctype = "PTM Scheduler"
    reference_name = "PTM-2024-2025-class_division-False-66116"

    add_mentions(
        comment_by, mentioned_users, content, reference_doctype, reference_name, name
    )


def compare_time(time_str, minute_difference):
    try:
        # Convert time string to datetime object
        time_obj = get_datetime(time_str)

        # Calculate the time before the current time by the specified minute difference
        current_time = now_datetime()
        comparison_time = add_to_date(current_time, minutes=minute_difference)

        # Check if the given time is within the specified difference before the current time
        return time_obj <= comparison_time
    except:
        # Log the error message
        frappe.log_error(f"Error comparing time for PTM Scheduler", frappe.get_traceback())
        return False


def get_user_id_of_instructor(teacher_id):
    employee = frappe.get_value('Instructor', teacher_id, 'employee')
    user_id = frappe.get_value('Employee', employee, 'user_id')
    
    if user_id:
        return user_id
    else:
        frappe.log_error(
            f"User ID not found for instructor {teacher_id}"
        )
        return None


@frappe.whitelist()
def notify_teacher_before_one_hour_job():
    minute_difference = 60

    # Retrieve PTM Scheduler records that need notification
    ptms = frappe.get_all(
        "PTM Scheduler",
        filters={"is_notified": 0, "date": today()},
        fields=[
            "name", "slot", "subject", "teacher", "division", "gmeet_link"
        ],
    )
    notifi_added = []
    content_template = "PTM Meeting is scheduled For <b>Division:</b> {0}, <b>Subject:</b> {1} at <b>{2}</b>.<br>Join: <a href='{3}'>{3}</a>"

    for ptm in ptms:
        slot = ptm.get("slot")
        if slot:
            # Extract the start time from the slot
            timef = slot.split("-")[0].strip() if "-" in slot else slot.strip()
            if timef and compare_time(timef, minute_difference):
                # Get the user ID of the teacher
                user_id_teacher = get_user_id_of_instructor(ptm.teacher)
                if user_id_teacher:
                    # Notify the teacher
                    notifi_added.append(ptm.name)
                    # Create a comment mentioning the teacher
                    content = content_template.format(ptm.division, ptm.subject, timef, ptm.gmeet_link)
                    add_mentions(
                        comment_by="Administrator",
                        user_id=user_id_teacher,
                        content=content,
                        reference_doctype="PTM Scheduler",
                        reference_name=ptm.name,
                        name=ptm.teacher,
                    )

    if notifi_added:
        # Update the is_notified flag in a batch
        sql_query = """UPDATE `tabPTM Scheduler` SET is_notified = 1 WHERE name IN %s"""
        frappe.db.sql(sql_query, (tuple(notifi_added),))
        frappe.db.commit()


def get_division_name_and_student_group_by_student_id(student_id):
    academic_year = current_academic_year()

    div_name = frappe.db.get_value(
        "Program Enrollment",
        {"student": student_id, "academic_year": academic_year, "docstatus": 1},
        "student_group",
    )
    if not div_name:
        return None

    sql = """ select parent,custom_group as stud_group ,custom_group_allocated as is_group from `tabStudent Group Student` where student = %(id)s and active = 1 and parent= %(div_name)s"""
    division_list = frappe.db.sql(
        sql, {"id": student_id, "div_name": div_name}, as_dict=1
    )

    if len(division_list) > 0:
        return division_list[0]
    return None


def get_datetime_from_time_slot(date, time_slot):
    # Parse the date string into a datetime object
    date_obj = date
    if time_slot:
        time_obj = datetime.datetime.strptime(time_slot.strip(), "%I:%M %p").time()

        # Combine date and time to create a datetime object
        datetime_obj = datetime.datetime.combine(date_obj, time_obj)

        return datetime_obj


@frappe.whitelist(allow_guest=True)
def get_upcoming_online_ptm_links(student_id):
    student_division_data = get_division_name_and_student_group_by_student_id(
        student_id
    )
    if not student_division_data:
        frappe.throw(
            "For Student {} Division is not found in system".format(student_id)
        )
    student_division = student_division_data.get("parent")
    student_group = student_division_data.get("stud_group")
    student_is_grp = student_division_data.get("is_group")
    print(student_division, student_group)
    if student_division:
        filterss = {
            "date": (">=", getdate(today())),
            "gmeet_link": ["is", "set"],
            "division": student_division,
        }
        if student_is_grp and (isinstance(student_group, int) or student_group):
            filterss["group"] = str(student_group)
        else:
            frappe.throw("No Student Group Allocated to Student")
        ptm_scheduler_list = frappe.get_all(
            "PTM Scheduler", filters=filterss, fields=["*"]
        )
        filterss2 = {
            "date": ("<", getdate(today())),
            "gmeet_link": ["is", "set"],
            "division": student_division,
        }
        ptm_scheduler_list2 = frappe.get_all(
            "PTM Scheduler", filters=filterss2, fields=["*"]
        )
        past_ptms = False
        if len(ptm_scheduler_list2):
            past_ptms = True
        if len(ptm_scheduler_list) > 0:
            for i in ptm_scheduler_list:
                i["datetime"] = get_datetime_from_time_slot(
                    i.get("date"), i.get("slot").split("-")[1]
                )
            ptm_scheduler_list = [
                item
                for item in ptm_scheduler_list
                if item.get("datetime") >= datetime.datetime.now()
            ]
            ptm_scheduler_list.sort(key=lambda x: x["datetime"])
            return {"data": ptm_scheduler_list, "past_ptms": past_ptms}
        return {"data": [], "past_ptms": past_ptms}


def get_list_of_students_from_division_list(division_list, student_group):
    print(division_list, student_group)
    sql = """select student from `tabStudent Group Student` where active = 1 and  parent in %(li)s and custom_group = %(group)s"""
    students_list = frappe.db.sql(
        sql, {"li": tuple(division_list), "group": student_group}, as_dict=1
    )
    return students_list


@frappe.whitelist()
def send_ptm_notifications_to_students():
    today_date = getdate(today())
    tomorrow_date = getdate(add_days(today(), 1))

    current_datetime = get_datetime().replace(second=0, microsecond=0)

    filterss = {
        # "is_gmeet_generated": 1,
        "gmeet_link": ["is", "set"],
        "date": ("between", [today_date, tomorrow_date]),
    }
    ptm_scheduler_list = frappe.get_all("PTM Scheduler", filters=filterss, fields=["*"])

    # Filter out datetimes before cutoff datetimes
    list_12hrs = []
    list_15mins = []
    list_5mins = []
    for item in ptm_scheduler_list:
        scheduled_datetime = get_datetime_from_time_slot(
            item.get("date"), item.get("slot").split("-")[0]
        )
        scheduled_datetime = scheduled_datetime.replace(second=0, microsecond=0)
        cutoff_datetime_12h = scheduled_datetime - datetime.timedelta(hours=12)
        cutoff_datetime_15m = scheduled_datetime - datetime.timedelta(minutes=15)
        cutoff_datetime_5m = scheduled_datetime - datetime.timedelta(minutes=5)
        if current_datetime == cutoff_datetime_12h:
            list_12hrs.append(item)
        elif current_datetime == cutoff_datetime_15m:
            list_15mins.append(item)
        elif current_datetime == cutoff_datetime_5m:
            list_5mins.append(item)

    already_notified = {}

    handle_notify(list_12hrs, "12 Hours", already_notified)
    handle_notify(list_15mins, "15 Minutes", already_notified)
    handle_notify(list_5mins, "5 Minutes", already_notified)


def handle_notify(time_data, time_inwords, already_notified):
    if not time_data or len(time_data) == 0:
        return

    for i in time_data:
        calculated_key = calculate_key(i)
        if not already_notified.get(calculated_key):
            students_lists = get_list_of_students_from_division_list(
                [i.get("division")], i.get("group")
            )
            notification_handler(
                [i.get("student") for i in students_lists], time_inwords
            )
            already_notified[calculated_key] = True


def calculate_key(ptm_data):
    division = ptm_data.get("division")
    group = ptm_data.get("group")
    time_slot = ptm_data.get("slot")
    date = ptm_data.get("date")
    return f"{division}#{group}#{time_slot}#{date}"


def notification_handler(student_data, time_inwords):
    # for student in division_data.get('student_ids'):
    #     send_notification(student_id=student,subject="Time to check your curriculum updates! :)")
    student_ids = tuple(student_data)
    if len(student_ids):
        guardian_details = frappe.db.sql(
            """SELECT gs.guardian as name, g.user
            FROM `tabStudent Guardian` gs
            INNER JOIN `tabGuardian` g ON g.name = gs.guardian
            WHERE gs.parent IN %(students)s """,
            {"students": student_ids},
            as_dict=1,
        )

        final_guardian_list = {}

        if len(guardian_details) > 0:
            for i in guardian_details:
                if i.user not in final_guardian_list:
                    final_guardian_list[i.user] = i

        if final_guardian_list:
            for guardian_name in final_guardian_list:
                send_notification_custom(
                    subject="Online PTM in {}. Please join in!".format(time_inwords),
                    user=guardian_name,
                )


def send_notification_custom(subject, user):
    if user:
        push_tokens = frappe.get_all(
            "Mobile Push Token", filters={"user_id": user}, fields=["token"]
        )
        for push_token in push_tokens:
            url = "https://exp.host/--/api/v2/push/send"
            payload = json.dumps(
                {
                    "to": push_token.get("token"),
                    "title": subject,
                    "data": {"url_path": f"/ptm-link"},
                    # "body": json.dumps({"url_path": f"/notice/{notice_id}?student={student_id}"})
                }
            )
            headers = {"Content-Type": "application/json"}
            requests.request("POST", url, headers=headers, data=payload)
