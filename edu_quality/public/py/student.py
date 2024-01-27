import frappe, random
import mysql.connector
from edu_quality.overrides import make_payment_request
import time 
from frappe.utils import today
import json
from datetime import datetime, timedelta

def autoname(doc, method=None):
    school_prefixes = {
        "Walnut School at Fursungi": "FU",
        "Walnut School at Shivane": "SH",
        "Walnut School at Wakad": "WA"
    }

    if doc.imported and doc.reference_number:
        prefix = school_prefixes.get(doc.school, '')
        doc_name = prefix + doc.reference_number
        doc.name = doc_name

    if doc.student_applicant:
        applicant = frappe.get_doc("Student Applicant",doc.student_applicant)
        prefix = frappe.get_value("School",applicant.school,'prefix')
        series = get_reference(doc.program)
        prefix += series
        if frappe.db.count("Student",[["name","Like",prefix + "%"]])>=99:
            prefix = prefix[:-2] + chr(ord(prefix[-2]) + 1)
            series = series[0] + chr(ord(series[1])+1)
            frappe.db.set_value("Program",applicant.program,'reference_series',series)
        if not prefix:
            prefix = "EDU-STU-2023-"
        count = frappe.db.count("Student",[["name","Like",prefix + "%"]]) + 1
        if count>9:
            prefix += str(count)
        else:
            prefix += "0" + str(count)
        doc.name = prefix

def before_insert(doc, method=None):
    frappe.flags.in_import = True

def get_reference(program):
    if not frappe.db.get_value("Academic Year",[["Academic Year","year_start_date","<=",today()],["Academic Year","year_end_date",">=",today()]],"rolled_over"):
        current_program = frappe.get_doc("Program",program)
        series = frappe.db.get_value("Program",{'school':current_program.school,"sequence":current_program.sequence-1},'reference_series')
        if not series:
            series = current_program.reference_series
            series = series[0] + chr(ord(series[1])+1) 
    else: 
        series = frappe.db.get_value("Program",program,'reference_series')
    return series

def update_student_group(p_e_doc,fee_structure=None):
    try:
        student_group = frappe.get_value("Program Enrollment",{"name":p_e_doc,"docstatus":1},'student_group')
        st = get_students_group(student_group)
        if st:
            program_e_d = frappe.get_doc("Student Group",student_group)
            program_e_d.students = []
            for item in st:
                program_e_d.append("students",item)
            program_e_d.save()
            if frappe.db.exists("Fee Schedule",{"fee_structure":fee_structure}):
                fee_schedule = frappe.get_value("Fee Schedule",{"fee_structure":fee_structure})
                frappe.db.set_value("Fee Schedule Student Group", {"parent":fee_schedule,"student_group":student_group},'total_students',len(st))
        return
    except Exception as e:
        frappe.throw(str(e))


def get_students_group(student_group):
    enrolled_students = frappe.get_all("Program Enrollment",{"student_group":student_group,"docstatus":1},['student','student_name'])
    if enrolled_students:
        student_list = []
        for s in enrolled_students:
            if frappe.db.get_value("Student", s.student, "enabled"):
                s.update({"active": 1})
            else:
                s.update({"active": 0})
            student_list.append(s)
        return student_list
    else:
        return []


def create_payment_request(fee,term=None):
    try:
        if not frappe.db.exists(
            "Payment Request",
            {"reference_doctype": "Fees", "reference_docname": fee.name},
        ):
            time.sleep(30)
            make_payment_request(
                party_type="Student",
                party=fee.student,
                dt="Fees",
                dn=fee.name,
                payment_term = term,
                recipient_id=frappe.get_value('Student',fee.student,'student_email_id'),
                submit_doc=True,
                use_dummy_message=True,
            )
    except Exception as e:
        frappe.logger("edu_quality").exception(e)


@frappe.whitelist()
def import_student(**kwargs):
    schools = frappe.get_list("School")
    school_db = {
        "Walnut School at Fursungi": "test_wal_db_WSF",
        "Walnut School at Shivane": "test_wal_db_WSS",
        "Walnut School at Wakad": "test_wal_db_WSW",
    }
    for db, school in enumerate(schools):
        database = school_db.get(school.name)
        frappe.enqueue(import_handler, queue="long", database=database,db=db)
    frappe.response['message'] = {
        "status": "success",
        "res": "Student Import Scheduled Successfully",
    }

def get_connection(database):
    mgr = frappe.get_single("MGR DB Details")
    host = mgr.host
    user = mgr.username
    password = mgr.get_password("password")
    connection = mysql.connector.connect(
        host=host, user=user, password=password, database=database
    )
    return connection


def import_handler(database,db):
    try:
        connection = get_connection(database)

        query = """SELECT *
                FROM walnut_student_info AS s
                JOIN walnut_class_info AS c ON s.admission_to = c.class_id
                JOIN division_master AS d ON s.division = d.division_id;
                """

        cursor = connection.cursor()
        cursor.execute(query)

        # fetach only no_of_students number of rows
        rows = cursor.fetchall()
        # Iterate over the rows and create Frappe records
        total_len = len(rows)
        for index, row in enumerate(rows):
            frappe.enqueue(insert_student, queue="long",row=row,column_names=cursor.column_names,doctype="Student",total_len=total_len,index=index,db=db,database=database)
            # insert_student(row, cursor.column_names, "Student")
            
    except Exception as e:
        frappe.logger("student_import").exception(e)
    

def insert_student(row, column_names, doctype,total_len,index,db,database):
    set_progress(index + 1, total_len,db, "Student Details")
    frappe_data = dict(zip(column_names, row))
    def get_data(key, default=None):
        return frappe_data.get(key, default)

    def capitalize_name(name):
        return get_data(name).capitalize() if get_data(name) else None

    first_name, middle_name, last_name = map(capitalize_name, ["first_name", "middle_name", "last_name"])
    student_name = f"{first_name} {middle_name or ''} {last_name}"
    student_email_id = f"{str(first_name).lower().replace(' ', '')}{random.randint(100, 999)}@walnut.edu"

    school_prefixes = {"Walnut School at Fursungi": "FU", "Walnut School at Shivane": "SH", "Walnut School at Wakad": "WA"}
    school_ids = {4: "Walnut School at Fursungi", 2: "Walnut School at Shivane", 5: "Walnut School at Wakad"}
    school_id = get_data("school_id")
    referral_school_id = get_data("referral_school_id")
    referral_school = school_ids.get(referral_school_id)
    school = school_ids.get(school_id)
    docname = school_prefixes.get(school, "") + get_data("refno")

    countries = [d["name"] for d in frappe.get_all("Country")]
    country = "India" if get_data("country") not in countries else get_data("country")

    date_of_leaving = get_data("leaving_date")
    joining_date = date_of_leaving - frappe.utils.datetime.timedelta(days=365) if date_of_leaving else None

    address_line_2 = f"{get_data('survey_number')}, {get_data('sub_area')}, {get_data('road')}, {get_data('area')}"

    category = get_data("category")

    class_mgr = get_data("class_name")
    program = get_program(class_mgr, school)
    new_doc_data = {
        "enabled": 1,
        "imported": 1,
        "form_code": get_data("form_code"),
        "form_id": get_data("form_id"),
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "first_name_marathi": get_data("fname_marathi"),
        "last_name_marathi": get_data("lname_marathi"),
        "date_of_birth": get_data("b_date"),
        "blood_group": get_data("blood_group", ""),
        "student_mobile_number": get_data("student_primary_contact_number"),
        "gender": get_data("gender"),
        "nationality": get_data("nationality"),
        "address_line_1": get_data("bld_house"),
        "address_line_2": address_line_2,
        "pincode": get_data("pin"),
        "city": get_data("city"),
        "state": get_data("state"),
        "country": country,
        "landmark": get_data("landmark"),
        "student_email_id": student_email_id,
        # "joining_date": joining_date,
        "date_of_leaving": date_of_leaving,
        "student_name": student_name,
        "school": school,
        "aadhaar_card_number": get_data("adhar_card_no"),
        "category": category,
        "school": school,
        "seeking_admission_in_class": program,
        "admission_to": program,
        "school_house": get_data("stud_house"),
        "saral_id": get_data("saral_id"),
        "cancel_photo_id": get_data("cancel_photo_id"),
        "tiffin_rack_no": get_data("tiffin_rack_no"),
        "catering": get_data("catering"),
        "caste": get_data("caste"),
        "subcaste": get_data("subcaste"),
        "minority": get_data("minority"),
        "mother_tongue": get_data("mother_tongue"),
        "student_referral_number": get_data("student_referral_refno"),
        "is_existing_student": get_data("student_isexistingstudent"),
        "existing_student_ref_number": get_data("student_existing_ref_number"),
        "is_handicap": 1 if get_data("handicap") else 0,
        "handicap": get_data("handicap"),
        "is_student_disabled": 1 if get_data("student_isdisability") else 0,
        "student_disability_name": get_data("student_disability_name"),
        "is_sibling_in_school": get_data("student_bro_sis_inschool"),
        "is_rte_student": get_data("stud_rte"),
        "single_parent_reason": get_data("single_parent_reason"),
        "religion": get_data("religion"),
        "reference_number": get_data("refno"),
        "custom_referrer_school": referral_school,
        "custom_referred_by": get_data("refer_by"),
        "day_care_contact": get_data("day_care_contact"),
        "bus_service_required": get_data("bus_service_required"),
        "has_allergies": 1 if get_data("allergies") else 0,
        "allergies": get_data("allergies"),
        "parent_divorced": get_data("if_divorced"),
        "single_parent_reason": get_data("single_parent_reason"),
        "doctype": doctype,
        "custom_mgr_status":map_student_status(get_data("status")),
        "custom_enquired_class":get_adimitad_class(database,get_data("class_admitted_to")),
        "custom_mothers_first_name":get_data("mother_f_name"),
    }
    frappe.flags.in_import = True
    frappe.logger("dddd").exception(frappe_data)
    if not frappe.db.exists(doctype, docname):
        new_doc = frappe.get_doc(new_doc_data)
        new_doc.insert(ignore_permissions=True)
        insert_program_enrollment(new_doc, frappe_data)
    else:
        if not frappe.db.exists("Program Enrollment", {"student":docname,"program":program}):
            old_doc = frappe.get_doc(doctype, docname)
            insert_program_enrollment(old_doc, frappe_data)
    frappe.flags.in_import = False


def map_student_status(id):
    data = {1:"New student",2:"Current student",3:"Cancelled",4:"Not attending",5:"Defaulter"}
    return data.get(id)

def insert_program_enrollment(student, data=None):
    try:
        program = student.seeking_admission_in_class
        academic_year = data.get("acadamic_year")
        academic_term = frappe.get_value("Academic Term", {"academic_year": academic_year})
        year_start_date = frappe.get_value("Academic Year",academic_year,"year_start_date")

        academic_year = get_academic_year(academic_year)
        school = student.school
        division = data.get("division_name")
        division_id = get_division(division, program, school, academic_year)

        program_enrollment = frappe.new_doc("Program Enrollment")
        program_enrollment.student = student.name
        program_enrollment.student_category = get_category(student.category)
        program_enrollment.student_name = student.student_name
        program_enrollment.custom_school = school
        program_enrollment.program = program
        program_enrollment.academic_year = academic_year
        program_enrollment.academic_term = academic_term
        program_enrollment.student_group = division_id
        program_enrollment.enrollment_date = year_start_date
        program_enrollment.save()
        program_enrollment.submit()
    except Exception as e:
        frappe.logger("program_enrollment").exception(e)
        cleaned_data = {key: value for key, value in data.items() if not isinstance(value, (datetime, timedelta))}
        error_obj={
                "filename":"program_enrollment",
                "object": cleaned_data,
                "Traceback": frappe.get_traceback(),
            },
        frappe.log_error(
        title="program_enrollment",
        message=json.dumps(error_obj),
        )

def get_category(category):
    if not category:
        return
    category_id = frappe.get_value("Student Category", {"category": category}, "name")
    if not category_id:
        category_id = frappe.new_doc("Student Category")
        category_id.category = category
        category_id.save(ignore_permissions=True)
    return category_id
    
    
def get_program(program_name, school):
    if not program_name:
        return None
    
    program = frappe.get_value("Program", {"program_name": program_name, "school": school})
    
    if not program:
        program = frappe.new_doc("Program")
        program.program_name = program_name
        program.school = school
        program.reference_series = "AC"
        program.insert(ignore_permissions=True)
    
    return program


def get_division(division, program, school, academic_year):
    # div = chr(int(division) + 24) if 40 <= int(division) <= 48 else int(division) - 24
    div = division
    div_filter = {
        "program": program,
        "custom_school": school,
        "academic_year": academic_year,
        "batch": div,
    }
    division = frappe.get_value("Student Group", div_filter)

    if not division:
        doc_properties = {
            "doctype": "Student Group",
            "program": program,
            "custom_school": school,
            "academic_year": academic_year,
            "student_group_name": div,
            "batch": div,
            "group_based_on": "Batch",
            "start_time": "10:00:00",
            "end_time": "10:00:00",
        }
        doc = frappe.get_doc(doc_properties)
        doc.insert(ignore_permissions=True)
        division = doc.name

    return division


def get_academic_year(academic_year):
    if not academic_year:
        return None
    academic_year_name = frappe.get_value("Academic Year", {"academic_year_name": academic_year})
    if academic_year_name:
        return academic_year_name

    year1, year2 = academic_year.split("-")
    doc = frappe.new_doc("Academic Year")
    doc.academic_year_name = academic_year
    doc.year_start_date = f"{year1}-04-01"
    doc.year_end_date = f"{year2}-03-31"
    doc.insert(ignore_permissions=True)
    return doc.name


def set_progress(current, total,db, job, expires_in_sec=300):
    progress = (current / total) * 100
    progress = f"{progress:.2f}%"
    frappe.cache().set_value(
        "student_import_status",
        {"progress": progress, "job": job,"db":db},
        expires_in_sec=expires_in_sec,
    )
    frappe.db.commit()

@frappe.whitelist()
def get_migration_progress():
    student_import_status = frappe.cache().get_value("student_import_status")
    if not student_import_status and is_migration_jobs_queued():
        student_import_status = {
            "progress": "Background Jobs Queued. Please be patient while it's processed.", 
            "job": None,
        }

    return student_import_status or {}

from frappe.utils.background_jobs import get_jobs
def is_migration_jobs_queued():
    jobs = get_jobs(site=frappe.local.site, key="job_name")[frappe.local.site]

    return any("student_import_" in job for job in jobs)  # noqa: 501


def get_adimitad_class(database, class_admitted_to):
    if not class_admitted_to:
        return None

    connection = get_connection(database)
    cursor = connection.cursor()

    cursor.execute(f"SELECT class_name FROM walnut_class_info WHERE class_id = {class_admitted_to}")
    row = cursor.fetchone()

    return row[0] if row else None
