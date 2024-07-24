import frappe
import json
from datetime import datetime, timedelta
from edu_quality.common.utils.progress import set_progress
import frappe, random
import mysql.connector
import datetime

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

    first_name, middle_name, last_name = map(capitalize_name, ["first_name", "father_f_name", "last_name"])
    student_name = f"{first_name} {middle_name or ''} {last_name}"

    school_prefixes = {"Walnut School at Fursungi": "FU", "Walnut School at Shivane": "SH", "Walnut School at Wakad": "WA"}
    school_ids = {4: "Walnut School at Fursungi", 2: "Walnut School at Shivane", 5: "Walnut School at Wakad"}
    school_id = get_data("school_id")
    referral_school_id = get_data("referral_school_id")
    referral_school = school_ids.get(referral_school_id)
    school = school_ids.get(school_id)
    refno = get_data("refno")
    docname = school_prefixes.get(school, "") + refno

    # student_email_id = f"{docname.lower()}@yopmail.com"

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
        # "student_mobile_number": "8770521949",
        "gender": get_data("gender"),
        "nationality": get_data("nationality"),
        "address_line_1": get_data("bld_house"),
        "address_line_2": address_line_2,
        "pincode": get_data("pin"),
        "city": get_data("city"),
        "state": get_data("state"),
        "country": country,
        "landmark": get_data("landmark"),
        "student_email_id": get_data("user_email"),
        # "student_email_id": student_email_id,
        "date_of_leaving": date_of_leaving,
        "joining_date": joining_date.strftime("%Y-%m-%d") if joining_date else None,
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
        "other_caste": get_data("other_caste"),
        "sub_caste": get_data("subcaste"),
        "other_sub_caste": get_data("other_subcaste"),
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
        "is_rte": get_data("stud_rte"),
        "single_parent_reason": get_data("single_parent_reason"),
        "religion": get_data("religion"),
        "reference_number": refno,
        "referrer_school": referral_school,
        "referred_by": get_data("refer_by"),
        "day_care_contact": get_data("day_care_contact"),
        "has_allergies": 1 if get_data("allergies") else 0,
        "allergies": get_data("allergies"),
        "parent_divorced": get_data("if_divorced"),
        "single_parent_reason": get_data("single_parent_reason"),
        "doctype": doctype,
        "student_status":map_student_status(get_data("status")),
        "enquired_class":get_data("admitted_class"),
        "gr_number":get_data("gr_number"),
        "gr_book_number":get_data("gr_book_number"),
        "height":get_data("height_start"),
        "weight":get_data("weight_start"),
        "birth_place":get_data("birthplace"),
        "confirm_for_next_year":"Yes" if get_data("confirm_next_year")==1 else "No",
        "last_school_attended": get_data("student_last_school_name"),
        "bus_service_required": get_data("bus_service_required"),
        "pickup_bus": get_data("pickup_bus"),
        "pickup_address": get_data("pickup_address"),
        # "special_instruction": get_data("spcl_instruction"),
        "drop_bus": get_data("drop_bus"),
        "drop_address": get_data("drop_address"),
        "source_name": get_data("ref_source_name"),
        "guardians": get_guardian(frappe_data),
        "whatsapp_number":get_data("student_sms_no"),
        # "whatsapp_number":"8770521949",
        "primary_contact":get_data("student_emergency_contact_no")
        # "primary_contact":"8770521949"
    }
    frappe.flags.in_import = True
    frappe.logger("dddd").exception(frappe_data)
    if not frappe.db.exists(doctype, docname):
        new_doc = frappe.get_doc(new_doc_data)
        new_doc.insert(ignore_permissions=True)
        if map_student_status(get_data("status")) not in ["Cancelled"]:
            insert_program_enrollment(new_doc, frappe_data,joining_date)
    else:
        if not frappe.db.exists("Program Enrollment", {"student":docname,"program":program}) and map_student_status(get_data("status")) !="Cancelled":
            old_doc = frappe.get_doc(doctype, docname)
            if map_student_status(get_data("status")) not in ["Cancelled"]:
                insert_program_enrollment(old_doc, frappe_data,joining_date)


def map_student_status(id):
    data = {1:"New student",2:"Current student",3:"Cancelled",4:"Not attending",6:"Defaulter",7:"Defaulter",8:"Alumni"}
    return data.get(id)

def insert_program_enrollment(student, data=None,joining_date=None):
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
        begin_batch_time = data.get("begintime")
        end_batch_time = data.get("endtime")
        division_id = get_division(division, program, school, academic_year,begin_batch_time,end_batch_time)
        roll_no = data.get("roll_no")

        program_enrollment = frappe.new_doc("Program Enrollment")
        program_enrollment.student = student.name
        program_enrollment.student_category = get_category(student.category)
        program_enrollment.student_name = student.student_name
        program_enrollment.custom_school = school
        program_enrollment.program = program
        program_enrollment.academic_year = academic_year
        program_enrollment.academic_term = academic_term
        program_enrollment.student_group = division_id
        program_enrollment.enrollment_date = joining_date.strftime("%Y-%m-%d") if joining_date else frappe.utils.nowdate()
        program_enrollment.tiffin_rack_no = data.get("tiffin_rack_no")
        program_enrollment.roll_no = roll_no
        program_enrollment.save()
        if student.student_status !="New student":
            program_enrollment.submit()
    except Exception as e:
        frappe.logger("student_import").exception(e)
        refno = data.get("refno")
        division = data.get("division_name")
        class_name = data.get("admitted_class")
        begin_batch_time = data.get("begintime")
        end_batch_time = data.get("endtime")
        division_batch = get_formated_date(begin_batch_time, end_batch_time)
        error_obj={
                "filename":"program_enrollment",
                "object": {"refno": refno, "division": division, "class_name": class_name, "division_batch": division_batch},
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
    
    
# CLASS_NAME_TO_GROUP = {
#     "Senior KG": "Senior KG",
#     "Junior KG": "Junior KG",
#     "Nursery": "Nursery",
#     "1": "Primary",
#     "2": "Primary",
#     "3": "Primary",
#     "4": "Primary",
#     "5": "Primary",
#     "6": "Secondary",
#     "7": "Secondary",
#     "8": "Secondary",
#     "9": "Secondary",
#     "10": "Secondary"
# }

# def get_class_group(class_name):
#     return CLASS_NAME_TO_GROUP.get(class_name)

def get_program(program_name, school):
    if not program_name:
        return None
    
    program = frappe.get_value("Program", {"program_name": program_name, "school": school})
    
    if not program:
        program = frappe.new_doc("Program")
        program.program_name = program_name
        program.school = school
        program.reference_series = "AC"
        program.class_group = "Senior KG"
        program.insert(ignore_permissions=True)
    
    return program


def get_division(division, program, school, academic_year,begin_batch_time,end_batch_time):
    div = division
    div_filter = {
        "program": program,
        "custom_school": school,
        "academic_year": academic_year,
        "batch": get_batch(begin_batch_time,end_batch_time),
        "student_group_name": div
    }
    division = frappe.get_value("Student Group", div_filter)

    if not division:
        doc_properties = {
            "doctype": "Student Group",
            "program": program,
            "custom_school": school,
            "academic_year": academic_year,
            "student_group_name": div,
            "batch": get_batch(begin_batch_time,end_batch_time),
            "group_based_on": "Batch"
        }
        doc = frappe.get_doc(doc_properties)
        doc.insert(ignore_permissions=True)
        division = doc.name

    return division

def get_batch(begin_batch_time,end_batch_time):
    batch_name = get_formated_date(begin_batch_time,end_batch_time)
    def create_batch(batch_name):
        batch_id = frappe.new_doc("Student Batch Name")
        batch_id.batch_name = batch_name
        batch_id.save()
        return batch_id.name

    batch_id = frappe.get_value("Student Batch Name", {'batch_name': batch_name})

    if not batch_id:
        batch_id = create_batch(batch_name)

    return batch_id

def get_formated_date(begin,end):
    begin_time = get_begin(begin)
    end_time = get_end(end)
    return str(begin_time+"-"+end_time)

def get_begin(delta):
    base_date = datetime.datetime(1, 1, 1)  
    result_time = (base_date + delta).time()
    formatted_time = result_time.strftime("%I:%M%p")
    return formatted_time

def get_end(delta):
    base_date = datetime.datetime(1, 1, 1)  
    result_time = (base_date + delta).time()
    formatted_time = result_time.strftime("%I:%M%p")
    return formatted_time

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


def create_guardian(relation, **kwargs):
    first_name = kwargs.get("f_name", "").capitalize()
    middle_name = kwargs.get("m_name", "").capitalize() if kwargs.get("m_name") else None
    last_name = kwargs.get("s_name", "").capitalize() if kwargs.get("s_name") else None
    guardian_name = f"{first_name} {last_name or ''}"
    mobile_no = kwargs.get("mobile_no")
    email_id = kwargs.get("email_id").lower() if kwargs.get("email_id") else None
    guardian = frappe.get_value("Guardian", {"guardian_name": guardian_name, "mobile_number": mobile_no})
    if first_name==' ':
        return None
    if not guardian:
        doc = {
            "doctype": "Guardian",
            "guardian_name": guardian_name,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "mobile_number": kwargs.get("mobile_no"),
            "email_address": email_id,
            "education": kwargs.get("education"),
            "occupation": kwargs.get("profession"),
            "annual_income": kwargs.get("annual_income"),
            "work_address": kwargs.get("office_address"),
            "company_name": kwargs.get("company_name"),
            "designation": kwargs.get("designation"),
        }
        guardian = frappe.get_doc(doc)
        guardian.insert(ignore_permissions=True)
    else:
        guardian = frappe.get_doc("Guardian", guardian)
    return {
        "guardian": guardian.name,
        "guardian_name": guardian.guardian_name,
        "relation": relation,
    }


def get_guardian(data):
    attributes = ["f_name", "m_name", "s_name", "email_id", "mobile_no", "education", "profession", "annual_income", "office_address", "company_name", "designation"]
    relations = ["Father", "Mother"]

    guardians = []
    for relation in relations:
        kwargs = {attr: data.get(f"{relation.lower()}_{attr}") for attr in attributes}
        guardian = create_guardian(relation, **kwargs)
        if guardian:
            guardians.append(guardian)
    return guardians
    

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
                    WCD.acadamic_year as acadamic_year_division,
                    WAD.admission_date,
                    WSP.father_f_name,
                    WSP.father_m_name,
                    WSP.father_s_name,
                    WSP.father_email_id,
                    WSP.father_mobile_no,
                    WSP.father_education,
                    WSP.father_profession,
                    WSP.father_annual_income,
                    WSP.father_office_address,
                    WSP.father_company_name,
                    WSP.father_designation,
                    WSP.mother_f_name,
                    WSP.mother_s_name,
                    WSP.mother_m_name,
                    WSP.mother_email_id,
                    WSP.mother_mobile_no,
                    WSP.mother_education,
                    WSP.mother_profession,
                    WSP.mother_annual_income,
                    WSP.mother_office_address,
                    WSP.mother_company_name,
                    WSP.mother_designation,
                    WSB.pickup_bus,
                    WSB.drop_bus,
                    WSB.pickup_address,
                    WSB.drop_address,
                    WSB.spcl_instruction,
                    CDR.begintime,
                    CDR.endtime,
                    WULD.user_email

                FROM
                    walnut_student_info wsi

                LEFT OUTER JOIN walnut_class_info WCI ON WCI.class_id = wsi.admission_to 
                LEFT OUTER JOIN walnut_class_info WCC ON WCC.class_id = wsi.class_admitted_to
                LEFT OUTER JOIN division_master WCD ON WCD.division_id = wsi.division
                LEFT OUTER JOIN stud_admission_details WAD ON WAD.ref_no = wsi.refno
                LEFT OUTER JOIN walnut_student_parent_details WSP ON WSP.student_id = wsi.form_id
                LEFT OUTER JOIN walnut_student_bus WSB ON WSB.student_id = wsi.form_id
                LEFT OUTER JOIN class_div_relation AS CDR ON CDR.class_id = wsi.admission_to AND CDR.division_id = wsi.division
                LEFT OUTER JOIN walnut_user_login_details as WULD ON WULD.user_name = wsi.refno AND WULD.school_id = wsi.school_id
                """
    return query