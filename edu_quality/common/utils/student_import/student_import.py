import frappe
import json
from datetime import datetime, timedelta
from edu_quality.common.utils.progress import set_progress
import frappe, random
import mysql.connector

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
    frappe.response['message'] = {"status": "success","res": "Student Import Scheduled Successfully"}

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
        query = get_sql_query()
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        for index, row in enumerate(rows):
            frappe.enqueue(insert_student, queue="long",row=row,column_names=cursor.column_names,doctype="Student",total_len=len(rows),index=index,db=db,database=database)
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
    student_email_id = f"{str(first_name).lower().replace(' ', '')}{random.randint(100, 999)}@walnutedu.in"

    mother_name = get_data('mother_f_name')
    father_name = get_data('father_f_name')

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
    joining_date = get_data("admission_date")

    address_line_2 = f"{get_data('survey_number')}, {get_data('sub_area')}, {get_data('road')}, {get_data('area')}"

    category = get_data("category")

    class_mgr = get_data("admission_class")
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
        "date_of_leaving": date_of_leaving,
        "joining_date": joining_date,
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
        "referrer_school": referral_school,
        "referred_by": get_data("refer_by"),
        "day_care_contact": get_data("day_care_contact"),
        "bus_service_required": get_data("bus_service_required"),
        "has_allergies": 1 if get_data("allergies") else 0,
        "allergies": get_data("allergies"),
        "parent_divorced": get_data("if_divorced"),
        "single_parent_reason": get_data("single_parent_reason"),
        "doctype": doctype,
        "student_status":map_student_status(get_data("status")),
        "enquired_class":get_data("admitted_class"),
        "guardian": get_guardian(father_name, mother_name),
    }
    frappe.flags.in_import = True
    frappe.logger("dddd").exception(frappe_data)
    if not frappe.db.exists(doctype, docname):
        new_doc = frappe.get_doc(new_doc_data)
        new_doc.insert(ignore_permissions=True)
        if map_student_status(get_data("status")) !="Cancelled":
            insert_program_enrollment(new_doc, frappe_data)
    else:
        if not frappe.db.exists("Program Enrollment", {"student":docname,"program":program}) and map_student_status(get_data("status")) !="Cancelled":
            old_doc = frappe.get_doc(doctype, docname)
            insert_program_enrollment(old_doc, frappe_data)
    frappe.flags.in_import = False


def map_student_status(id):
    data = {1:"New student",2:"Current student",3:"Cancelled",4:"Not attending",5:"Defaulter"}
    return data.get(id)

def insert_program_enrollment(student, data=None):
    try:
        program = student.seeking_admission_in_class
        if data.get("status")==1:
            academic_year = "2024-2025"
        else:
            academic_year = "2023-2024"
        # academic_year = data.get("acadamic_year_division")
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


def create_guardian(first_name, relation, middle_name=None, last_name=None, mobile_no=None, email_id=None, education=None, occupation=None, annual_income=None):
    guardian = frappe.get_value("Guardian", {"guardian_name": first_name})
    if not guardian:
        guardian = frappe.new_doc("Guardian", {
            "guardian_name": first_name,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "mobile_number": mobile_no,
            "email_address": email_id,
            "education": education,
            "occupation": occupation,
            "annual_income": annual_income
        })
        guardian.insert(ignore_permissions=True)
    return {
        "guardian": guardian,
        "guardian_name": first_name,
        "guardian_relation": relation,
    }

def get_guardian(father_name, mother_name):
    return [create_guardian(name, relation) for name, relation in [(father_name, "Father"), (mother_name, "Mother")] if name]

    

def get_sql_query():
    query = """SELECT
                    wsi.form_id,
                    wsi.ame_no,
                    wsi.school_id,
                    wsi.first_name,
                    wsi.fname_marathi,
                    wsi.lname_marathi,
                    wsi.status,
                    wsi.catering,
                    wsi.academic_year,
                    wsi.last_name,
                    wsi.father_f_name,
                    wsi.mother_f_name,
                    wsi.adhar_card_no,
                    wsi.gender,
                    wsi.nationality,
                    wsi.mother_tongue,
                    wsi.religion,
                    wsi.category,
                    wsi.caste,
                    wsi.subcaste,
                    wsi.b_date,
                    wsi.b_city,
                    wsi.b_state,
                    wsi.b_country,
                    wsi.admission_to,
                    wsi.blood_group,
                    wsi.bld_house,
                    wsi.survey_number,
                    wsi.sub_area,
                    wsi.road,
                    wsi.area,
                    wsi.pin,
                    wsi.city,
                    wsi.country,
                    wsi.state,
                    wsi.landmark,
                    wsi.landline_number,
                    wsi.other_nationality,
                    wsi.other_mother_tongue,
                    wsi.other_religion,
                    wsi.other_category,
                    wsi.other_caste,
                    wsi.other_subcaste,
                    wsi.parent_status,
                    wsi.child_status,
                    wsi.bus_service_required,
                    wsi.student_bro_sis_inschool,
                    wsi.student_bro_sis_ref_no,
                    wsi.student_isdisability,
                    wsi.student_disability_name,
                    wsi.student_primary_contact_number,
                    wsi.student_sms_no,
                    wsi.student_emergency_contact_no,
                    wsi.student_isexistingstudent,
                    wsi.student_existing_ref_number,
                    wsi.student_last_school_name,
                    wsi.student_last_school_address,
                    wsi.student_acknowledge,
                    wsi.stud_ssc_marks,
                    wsi.stud_board,
                    wsi.stud_outofmarks,
                    wsi.stud_passyear,
                    wsi.form_code,
                    wsi.refno,
                    wsi.institude_id,
                    wsi.division,
                    wsi.stud_rte,
                    wsi.stud_amne,
                    wsi.isonline,
                    wsi.roll_no,
                    wsi.day_care_contact,
                    wsi.web_password,
                    wsi.child_total,
                    wsi.child_order,
                    wsi.refer_by,
                    wsi.contact_other,
                    wsi.confirm_next_year,
                    wsi.pickup_bus,
                    wsi.drop_bus,
                    wsi.height_start,
                    wsi.hegiht_end,
                    wsi.weight_start,
                    wsi.weight_end,
                    wsi.bmi_start,
                    wsi.bmi_end,
                    wsi.remark_bmi_start,
                    wsi.remark_bmi_end,
                    wsi.stud_house,
                    wsi.nss,
                    wsi.ncc,
                    wsi.sports,
                    wsi.culture,
                    wsi.birth_cert,
                    wsi.lc_submit,
                    wsi.bonafied_cnt,
                    wsi.createdby,
                    wsi.created,
                    wsi.modifiedby,
                    wsi.modified,
                    wsi.birthplace,
                    wsi.app_access,
                    wsi.gr_number,
                    wsi.leaving_date,
                    wsi.gr_book_number,
                    wsi.shift,
                    wsi.category_cert,
                    wsi.disabilty_cert,
                    wsi.adhar_card_cert,
                    wsi.minority,
                    wsi.cbse_reg_no,
                    wsi.name_validation,
                    wsi.handicap,
                    wsi.form_status,
                    wsi.pref_batch_time,
                    wsi.lead_type,
                    wsi.class_admitted_to,
                    wsi.classroom_groups,
                    wsi.status_reason,
                    wsi.student_referral,
                    wsi.student_referral_refno,
                    wsi.referral_school_id,
                    wsi.student_photo,
                    wsi.saral_id,
                    wsi.allergies,
                    wsi.other_allergies,
                    wsi.single_parent_reason,
                    wsi.if_divorced,
                    wsi.court_order_doc,
                    wsi.next_cancel_letter,
                    wsi.cancel_photo_id,
                    wsi.tiffin_rack_no,
                    wsi.walnut_enquiry,
                    wsi.ref_parent_name,
                    wsi.ref_parent_no,
                    wsi.ref_source_name,
                    WCI.class_name as admission_class,
                    WCC.class_name as admitted_class,
                    WCD.division_name,
                    WCD.acadamic_year as acadamic_year_division
                    WAD.admission_date,
                FROM
                    walnut_student_info wsi

                INNER JOIN walnut_class_info WCI ON WCI.class_id = wsi.admission_to 
                INNER JOIN walnut_class_info WCC ON WCC.class_id = wsi.class_admitted_to
                INNER JOIN division_master WCD ON WCD.division_id = wsi.division;
                INNER JOIN stud_admission_details WAD ON WAD.refno = wsi.refno;
                """
    return query
