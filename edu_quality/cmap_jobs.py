import frappe
from frappe.utils.data import *

import datetime
import requests
import json


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
        time_obj = datetime.datetime.strptime(time_str, "%I:%M %p")

        # Calculate half an hour before the current time
        half_hour_before = datetime.datetime.now() - datetime.timedelta(
            minutes=minute_difference
        )

        # Check if the given time is half an hour or less before the current time
        return time_obj <= half_hour_before
    except Exception as e:
        print(f"Error comparing time: {e}")
        return False


def get_user_id_of_instructor(teacher_id):
    try:
        instructor = frappe.get_doc("Instructor", teacher_id)
        employee = frappe.get_doc("Employee", instructor.employee)
        return employee.user_id
    except Exception as e:
        frappe.log_error(
            f"Error in getting user ID for instructor {teacher_id}: {str(e)}"
        )
        return None


@frappe.whitelist()
def notify_teacher_before_half_hour_job():
    minute_difference = 30
    data = frappe.get_all(
        "PTM Scheduler",
        filters={"is_notified": 0, "date": frappe.utils.today()},
        fields=[
            "name",
            "slot",
            "subject",
            "teacher",
            "date",
            "division",
            "branch",
            "day",
            "gmeet_link"
        ],
    )
    notifi_added = []
    content = "PTM Meeting is scheduled soon. Please be prepared. <a href='{0}'>{0}</a>"

    # Iterate over PTM Scheduler records
    for record in data:
        slot = record.get("slot")
        if slot:
            # Extract the end time from the slot string
            timef = slot.split("-")[1].strip() if "-" in slot else slot.strip()
            if timef and compare_time(timef, minute_difference):
                # Get the teacher ID and corresponding user ID
                teacher_id = record.get("teacher")
                user_id_teacher = get_user_id_of_instructor(teacher_id)
                if user_id_teacher:
                    notifi_added.append(record.get("name"))
                    # Add mention with the notification content
                    add_mentions(
                        comment_by="Administrator",
                        user_id=user_id_teacher,
                        content=content.format(record.get("gmeet_link")),
                        reference_doctype="PTM Scheduler",
                        reference_name=record.get("name"),
                        name=teacher_id,
                    )

    # Update is_notified flag for notified records
    if notifi_added:
        # Construct SQL query to update is_notified flag
        sql = """UPDATE `tabPTM Scheduler` SET is_notified = 1 WHERE name IN %(li)s"""
        frappe.db.sql(sql, {"li": tuple(notifi_added)})
        frappe.db.commit()


def get_division_name_and_student_group_by_student_id(student_id):
    sql = """ select parent,custom_group as stud_group ,custom_group_allocated as is_group from `tabStudent Group Student` where student = %(id)s and active = 1"""
    division_list = frappe.db.sql(sql, {"id": student_id}, as_dict=1)
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


@frappe.whitelist()
def get_upcoming_online_ptm_links(student_id):
    student_division_data = get_division_name_and_student_group_by_student_id(student_id)
    if  not student_division_data:
        frappe.throw("For Student {} Division is not found in system".format(student_id))
    student_division = student_division_data.get('parent')
    student_group = student_division_data.get('stud_group')
    student_is_grp = student_division_data.get('is_group')
    if student_division:
        filterss = {'date':('>=',getdate(today())),'is_gmeet_generated':1,'division':student_division}
        if student_is_grp and student_group:
            filterss['group'] = str(student_group)
        else:
            frappe.throw('No Student Group Allocated to Student')    
        ptm_scheduler_list = frappe.get_all('PTM Scheduler',filters=filterss,fields=['*'])
        if len(ptm_scheduler_list)>0:
            for i in ptm_scheduler_list:
                i['datetime'] = get_datetime_from_time_slot(i.get('date'),i.get('slot').split("-")[1])
            ptm_scheduler_list = [ item for item in ptm_scheduler_list if item.get('datetime') >= datetime.datetime.now()]
            ptm_scheduler_list.sort(key=lambda x: x['datetime'])
            return ptm_scheduler_list
        return []


def get_list_of_students_from_division_list(division_list):
    sql = """select student from `tabStudent Group Student` where active = 1 and  parent in %(li)s"""
    students_list = frappe.db.sql(sql,{'li':tuple(division_list)},as_dict=1)
    return students_list

@frappe.whitelist()
def send_ptm_notifications_to_students():
    today_date = getdate(today())
    tomorrow_date = getdate(add_days(today(), 1))
    # Get current datetime
    current_datetime = get_datetime().replace(second=0, microsecond=0)
    filterss = {
        'is_gmeet_generated': 1,
        'date': ('between', [today_date, tomorrow_date])
    }
    ptm_scheduler_list = frappe.get_all('PTM Scheduler',filters=filterss,fields=['*'])
   
    # Filter out datetimes before cutoff datetimes
    list_12hrs = []
    list_15mins= []
    list_5mins = []
    for item in ptm_scheduler_list:
        scheduled_datetime = get_datetime_from_time_slot(item.get('date'), item.get('slot').split("-")[0])
        scheduled_datetime = scheduled_datetime.replace(second=0, microsecond=0)
        cutoff_datetime_12h = scheduled_datetime - datetime.timedelta(hours=12)
        cutoff_datetime_15m = scheduled_datetime - datetime.timedelta(minutes=15)
        cutoff_datetime_5m = scheduled_datetime - datetime.timedelta(minutes=5)
        if (current_datetime == cutoff_datetime_12h):
            list_12hrs.append(item)
        elif current_datetime == cutoff_datetime_15m:
            list_15mins.append(item)
        elif current_datetime == cutoff_datetime_5m:
            list_5mins.append(item)
    if len(list_12hrs)>0:
        division_list =  [i.get('division') for i in list_12hrs]   
        students_lists = get_list_of_students_from_division_list(division_list)
        if len(students_lists):
            notification_handler([i.get('student') for i in students_lists ],"12 Hours")
    
    if len(list_15mins)>0:
        division_list =  [i.get('division') for i in list_15mins]   
        students_lists = get_list_of_students_from_division_list(division_list)
        if len(students_lists):
            notification_handler([i.get('student') for i in students_lists ],"15 Minutes")         
    
    if len(list_5mins)>0:
        division_list =  [i.get('division') for i in list_5mins]   
        students_lists = get_list_of_students_from_division_list(division_list)
        if len(students_lists):
            notification_handler([i.get('student') for i in students_lists ],"5 Minutes")                 
            

    

def notification_handler(student_data,time_inwords):
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
        print(guardian_details)

        final_guardian_list = {}

        if len(guardian_details) > 0:
            for i in guardian_details:
                if i.name not in final_guardian_list:
                    final_guardian_list[i.name] = i

        if final_guardian_list:
            for guardian_name, guardian_data in final_guardian_list.items():
                send_notification_custom(
                    subject="Online PTM in {}. Pl join in!".format(time_inwords),
                    guardian=guardian_data,
                )


def send_notification_custom(subject, guardian):
    user = guardian.get("user")
    print(subject)
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
                    "data": {"url_path": f"/ptm-links"},
                    # "body": json.dumps({"url_path": f"/notice/{notice_id}?student={student_id}"})
                }
            )
            headers = {"Content-Type": "application/json"}
            requests.request("POST", url, headers=headers, data=payload)
            