import frappe, random
import mysql.connector
from edu_quality.overrides import make_payment_request
import time 

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
        series = frappe.get_value("Program",applicant.program,'reference_series')
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
                doc = frappe.get_doc("Fee Schedule Student Group", {"parent":fee_schedule,"student_group":student_group})
                doc.total_students = len(st)
                doc.save()
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
                recipient_id=fee.student_email,
                submit_doc=True,
                use_dummy_message=True,
            )
    except Exception as e:
        frappe.logger("edu_quality").exception(e)


@frappe.whitelist()
def import_student(**kwargs):
    school = kwargs.get("school")
    program = kwargs.get("program")
    division = kwargs.get("division")
    academic_year = kwargs.get("academic_year")
    if school == "Walnut School at Fursungi":
        database = "test_wal_db_WSF"
    elif school == "Walnut School at Shivane":
        database = "test_wal_db_WSS"
    elif school == "Walnut School at Wakad":
        database = "test_wal_db_WSW"

    data = {
        "database": database,  # "test_wal_db_WSF",
        "school": school,
        "program": program,
        "division": division,
        "academic_year": academic_year,
    }
    frappe.enqueue(import_handler, queue="long", timeout=1500, **data)
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


def import_handler(database, school, program=None, division=None, academic_year=None):
    try:
        academic_year = academic_year or ""
        div = division.split("-")[0] if division else ""
        div = get_division(div)
        class_admitted_to = program.split("-")[0] if program else ""

        connection = get_connection(database)


        query = f"SELECT * FROM walnut_student_info where academic_year='{academic_year}'"
        if program:
            query += f" and class_admitted_to='{class_admitted_to}'"
        if division:
            query += f" and division='{div}'"
            
        cursor = connection.cursor()
        cursor.execute(query)

        # fetach only no_of_students number of rows
        rows = cursor.fetchall()
        # Iterate over the rows and create Frappe records

        for row in rows:
            insert_student(row, cursor.column_names, "Student", school, program, division, academic_year)
            
    except Exception as e:
        frappe.logger("student_import").exception(e)
    

def insert_student(row, column_names, doctype, school, program, division, academic_year):
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
        "joining_date": joining_date,
        "date_of_leaving": date_of_leaving,
        "student_name": student_name,
        "school": school,
        "aadhaar_card_number": get_data("aadhaar_card_number"),
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
    }
    frappe_data['division'] = division
    frappe_data['academic_year'] = academic_year
    frappe.flags.in_import = True
    if not frappe.db.exists(doctype, docname):
        new_doc = frappe.get_doc(new_doc_data)
        new_doc.insert(ignore_permissions=True)
        insert_program_enrollment(new_doc, frappe_data)
    frappe.flags.in_import = False


def insert_program_enrollment(student, data=None):
    program = student.seeking_admission_in_class
    academic_year = data.get("academic_year")
    academic_term = frappe.get_value("Academic Term", {"academic_year": academic_year})
    student_group = data.get('division')
    program_enrollment = frappe.new_doc("Program Enrollment")
    program_enrollment.student = student.name
    program_enrollment.student_category = student.category
    program_enrollment.student_name = student.student_name
    program_enrollment.school = student.school
    program_enrollment.program = program
    program_enrollment.academic_year = academic_year
    program_enrollment.academic_term = academic_term
    program_enrollment.student_group = student_group
    program_enrollment.save()
    program_enrollment.submit()


def get_division(grade):
    if grade.isalpha():
        return ord(grade) - 24
    else:
        return int(grade) + 24