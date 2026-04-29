# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import calendar
from datetime import datetime, timedelta
import json
from weasyprint import HTML
from edu_quality.public.py.utils import (
    gen_qr_code_b64_transparent,
)


class StudentAttendanceSheet(Document):
    pass


@frappe.whitelist()
def get_months():

    months = []
    for i in range(1, 13):
        months.append(
            {"value": calendar.month_name[i], "label": calendar.month_name[i]}
        )
    return months


@frappe.whitelist()
def get_days_in_month(month_name, academic_year, as_date=False, month=1, year=None):
    month_number = list(calendar.month_name).index(month_name.capitalize())
    year = int(get_year(academic_year, month_number))

    # Get the number of days in the month
    _, num_days = calendar.monthrange(year, month_number)

    # Generate a list of days
    days = [{"textContent": str(day)} for day in range(1, num_days + 1)]
    if as_date:
        days = {datetime(year, month, day).date() for day in range(1, num_days + 1)}
    return days


@frappe.whitelist()
def get_students(
    program,
    division,
):
    students = frappe.get_all(
        "Program Enrollment",
        filters={
            "student_group": division,
            "program": program,
            "docstatus": 1,
            "custom_status": ["in", ["Current student", "Defaulter"]],
        },
        fields=[
            "student.reference_number",
            "student.first_name",
            "student.last_name",
            "roll_no",
            "student.name",
        ],
        order_by="roll_no ASC",
    )

    return sorted(students, key=sorting_key)


def get_holidays(start_date, end_date, program, format_as_date=True):
    holidays = []
    event_qb = frappe.qb.DocType("Event")
    event_class_qb = frappe.qb.DocType("Event Class")
    events = (
        frappe.qb.from_(event_qb)
        .inner_join(event_class_qb)
        .on(event_class_qb.parent == event_qb.name)
        .select(event_qb.starts_on, event_qb.ends_on)
        .where(
            (event_class_qb["class"] == program)
            & (
                ((event_qb.starts_on >= start_date) & (event_qb.ends_on <= end_date))
                | (
                    (event_qb.starts_on <= start_date)
                    & (event_qb.ends_on >= start_date)
                )
            )
            & (event_qb.custom_holiday == 1)
        )
        .run(as_dict=True)
    )

    if len(events) != 0:
        for event in events:
            days = get_included_days(event.starts_on, event.ends_on, format_as_date)
            holidays.extend(days)
    return holidays


@frappe.whitelist()
def get_data(month_name, academic_year, program, division):
    students = get_students(program, division)
    days = get_days_in_month(month_name, academic_year)
    month = datetime.strptime(month_name, "%B").month
    year = int(get_year(academic_year, month))
    day_numbers = [int(day["textContent"]) for day in days]
    holidays = []

    start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
    end_date = (
        (datetime(year, month + 1, 1) - timedelta(days=1)).strftime("%Y-%m-%d")
        if month < 12
        else datetime(year, month, 31).strftime("%Y-%m-%d")
    )

    holidays = get_holidays(start_date, end_date, program, True)
    holidays = [holiday.day for holiday in holidays if holiday.month == month]

    result = {}
    for student in students:

        student_days = [{day: "H" if day in holidays else ""} for day in day_numbers]
        result[student["reference_number"]] = student_days
    first_letter_division = division[0].upper() if division else ""
    attendance_data = frappe.get_all(
        "Attendance Entry",
        filters={
            "class": program,
            "division": ["in", [division, first_letter_division]],
            "date": ["between", [start_date, end_date]],
            "status": ["!=", "Holiday"],
            "docstatus": ["in", [0, 1]],
        },
        fields=["status", "date", "student.reference_number", "name", "docstatus"],
    )
    if attendance_data:
        filtered_data = [
            entry
            for entry in attendance_data
            if entry["date"].year == year and entry["date"].month == month
        ]
        for entry in filtered_data:

            ref_number = entry["reference_number"]
            status = (
                get_attendance_status(entry["status"], "code")
                if entry.docstatus or entry["status"]
                else get_latest_status(entry)
            )
            day = str(entry["date"].day)
            if ref_number not in result:
                continue
            for day_status in result[ref_number]:
                if int(day) in day_status:
                    day_status[day] = status
                    break

    return {"table_data": result, "holidays": holidays}


@frappe.whitelist()
def save_attendance(**data):
    month_name = data.get("month_name")
    academic_year = data.get("academic_year")
    month = datetime.strptime(month_name, "%B").month
    year = int(get_year(academic_year, month))
    program = data.get("program")
    division = data.get("division")
    attendance_data = json.loads(data.get("attendance_data"))
    error = {}

    for student_id, days in attendance_data.items():
        for day_obj in days:
            day, value = next(iter(day_obj.items()))
            if value not in ["P", "A"]:
                error = {
                    "msg": "Attendance entry is invalid. Please input either 'P' for present or 'A' for absent.",
                    "error": 1,
                }
            try:
                student = frappe.get_doc("Student", {"name": student_id})
                date = frappe.utils.data.getdate(f"{year}-{month:02d}-{day}")

                existing_entry = frappe.db.get_value(
                    "Attendance Entry",
                    {
                        "date": date,
                        "student": student.name,
                        "class": program,
                        "division": division,
                    },
                    ["docstatus", "name"],
                )

                if existing_entry:
                    doc_status = existing_entry[0]
                    name = existing_entry[1]
                    if doc_status == 0:
                        frappe.db.set_value(
                            "Attendance Entry",
                            name,
                            "status",
                            get_attendance_status(value, "name"),
                        )
                    elif doc_status == 1:
                        error = {
                            "msg": "Submitted entries cannot be modified",
                            "error": 1,
                        }
                    continue

                doc = frappe.get_doc(
                    {
                        "doctype": "Attendance Entry",
                        "date": date,
                        "student": student.name,
                        "status": get_attendance_status(value, "name"),
                        "class": program,
                        "division": division,
                    }
                )

                doc.insert()

            except:
                pass

    if error:
        return error
    return {"msg": "Attendance saved successfully", "error": 0}


def get_year(academic_year, month):
    academic_year = frappe.get_doc("Academic Year", academic_year)
    year_start_date = academic_year.year_start_date
    year_end_date = academic_year.year_end_date
    # calculate all months and their years between start and end date including them
    months = []
    while year_start_date <= year_end_date:
        months.append(year_start_date)
        year_start_date = year_start_date.replace(
            month=year_start_date.month % 12 + 1,
            year=year_start_date.year + year_start_date.month // 12,
        )
    # make a hash of months and their years
    print(months)
    month_year_hash = {month.month: month.year for month in months}
    print(month_year_hash)
    return month_year_hash[month]


@frappe.whitelist()
def submit_attendance(**data):

    month_name = data.get("month_name")
    academic_year = data.get("academic_year")
    month = datetime.strptime(month_name, "%B").month
    year = int(get_year(academic_year, month))

    program = data.get("program")
    division = data.get("division")
    start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
    end_date = (
        (datetime(year, month + 1, 1) - timedelta(days=1)).strftime("%Y-%m-%d")
        if month < 12
        else datetime(year, month, 31).strftime("%Y-%m-%d")
    )
    holidays = get_holidays(start_date, end_date, program, True)
    unique_dates = get_days_in_month(month_name, academic_year, True, month, year)

    attendance_entries = frappe.get_all(
        "Attendance Entry",
        filters={
            "date": ["between", [start_date, end_date]],
            "docstatus": 0,
            "class": program,
            "division": division,
        },
        fields=["date", "name", "student"],
    )

    for entry in attendance_entries:
        attendance_entry = frappe.get_doc(
            "Attendance Entry",
            entry["name"],
            [
                "name",
                "status",
            ],
        )

        if not attendance_entry.get("status"):
            status = get_latest_status(entry)
            attendance_entry.status = (
                "Present" if status not in ["A", "S"] else "Absent"
            )
        attendance_entry.submit()

    all_students = frappe.get_all(
        "Program Enrollment",
        filters={
            "student_group": division,
            "program": program,
            "custom_status": ["in", ["Current student", "Defaulter"]],
        },
        fields=["student"],
    )

    all_student_names = {student["student"] for student in all_students}
    for date in unique_dates:
        if date in holidays:
            continue

        marked_students = {
            entry["student"] for entry in attendance_entries if entry["date"] == date
        }
        unmarked_students = all_student_names - marked_students

        for student in unmarked_students:
            existing_entry = frappe.get_all(
                "Attendance Entry",
                filters={
                    "student": student,
                    "date": date,
                    "docstatus": ["in", [0, 1]],  # Check for already submitted entries
                },
                fields=["name"],
            )

            for exist in existing_entry:
                doc = frappe.get_doc("Attendance Entry", exist)
                if doc.docstatus == 1:
                    continue
                doc.status = "Present"
                doc.save()
                doc.submit()

            if not existing_entry:
                new_entry = frappe.get_doc(
                    {
                        "doctype": "Attendance Entry",
                        "student": student,
                        "date": date,
                        "status": "Present",
                        "class": program,
                        "docstatus": 1,  # Assuming 1 is the status for submitted
                        "division": division,
                    }
                )
                new_entry.insert()
                new_entry.submit()

    return "Attendance submitted successfully"


@frappe.whitelist()
def check_attendance_entry(**data):
    month_name = data.get("month_name")
    academic_year = data.get("academic_year")
    month = datetime.strptime(month_name, "%B").month
    year = int(get_year(academic_year, month))
    program = data.get("program")
    start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
    end_date = (
        (datetime(year, month + 1, 1) - timedelta(days=1)).strftime("%Y-%m-%d")
        if month < 12
        else datetime(year, month, 31).strftime("%Y-%m-%d")
    )
    filters = {
        "date": ["between", [start_date, end_date]],
        "docstatus": 0,
        "class": program,
        "status": ["=", ""],
    }

    # Query to check if any document exists with the given filters
    attendance_entries = frappe.get_list(
        "Attendance Entry",
        filters=filters,
        fields=[
            "name",
            "absent_and_delays.status",
        ],  # Only retrieve the document name for existence check
    )

    # Check if the list is not empty
    if attendance_entries:
        return True
    else:
        return False


@frappe.whitelist()
def get_divisions(academic_year, program):
    return frappe.get_all(
        "Student Group",
        filters={"academic_year": academic_year, "program": program},
        fields=["name"],
    )


def get_included_days(start_on, end_on, format_as_date=True):

    if end_on is None or not isinstance(end_on, datetime):
        end_on = start_on

    start_date = start_on.date()
    end_date = end_on.date()

    days = []
    current_date = start_date
    while current_date <= end_date:
        if format_as_date:
            days.append(current_date)
        else:
            days.append(current_date.day)
        current_date += timedelta(days=1)

    return days


def get_attendance_status(val, return_type):
    name_mapping = {
        "P": "Present",
        "H": "Holiday",
        "L": "Late",
        "A": "Absent",
        "E": "Early Pickup",
        "S": "Sick",
    }

    short_mapping = {v: k for k, v in name_mapping.items()}

    if return_type == "name":
        return name_mapping.get(val.upper(), "")
    else:
        return short_mapping.get(val, "")


@frappe.whitelist()
def generate(**kwargs):
    try:
        base_url = frappe.utils.get_url()

        tables = kwargs.get("tables")

        for parent_table in tables:
            table = parent_table.get("table")
            rows = table.get("rows")

        for index in range(len(rows)):
            row = rows[index]
            if "value=A" in row:
                rows[index] = row.replace("value=A", "value= ")
            elif "value=L" in row:
                rows[index] = row.replace("value=L", "value= ")
            elif "value=E" in row:
                rows[index] = row.replace("value=E", "value= ")
            elif "value=S" in row:
                rows[index] = row.replace("value=S", "value= ")

        update_tables_with_qr_code(tables)

        template = frappe.render_template(
            "edu_quality/templates/pdf/student_attendance_sheet.html",
            {"tables": tables},
        )
        html = HTML(string=template, base_url=base_url)

        main_doc = html.render()
        main_pdf = main_doc.write_pdf()

        frappe.local.response.filename = "Temporary Id Card.pdf".format(
            name="Temporary Id Card.pdf".replace(" ", "-").replace("/", "-")
        )
        frappe.local.response.filecontent = main_pdf
        frappe.local.response.type = "pdf"
    except Exception as e:
        return frappe.throw(e)


def update_tables_with_qr_code(tables):
    for table in tables:
        qr_data = {
            "class": table["class"],
            "division": table["division"],
            "month": table["month"],
            "year": table["year"],
        }
        table["qr_code"] = gen_qr_code_b64_transparent(qr_data)


def get_latest_status(entry):
    latest_entry = frappe.get_all(
        "Absent and Delay",
        filters={
            "parent": entry["name"],
        },
        fields=["status"],
        order_by="timestamp desc",
        limit=1,
    )

    if latest_entry:
        status = latest_entry[0]["status"]
        if status:
            status_upper = status.upper()
            if "EARLY" in status_upper:
                return "E"
            elif "LATE" in status_upper:
                return "L"
            elif "SICK" in status_upper:
                return "S"
            elif "ABSENT" in status_upper:
                return "A"

    return ""


def sorting_key(student):
    roll_no = student["roll_no"]
    try:
        return (0, int(roll_no))  # Valid roll_no
    except (TypeError, ValueError):
        return (1, roll_no)
