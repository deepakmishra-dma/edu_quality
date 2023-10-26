import frappe
from frappe.utils.file_manager import save_file
import json
import requests
import datetime
import time
import uuid
import pytz

CONFIG = {
    "WALSH_API_BASE": "https://testwalsh.walnutedu.in/indexCI.php",
    "MGR_API_BASE": "https://test.walnutedu.in/indexCI.php",
}


def get_class_without_std(txt):
    if not txt:
        return " "
    if "Std. " in txt:
        return txt.split("Std. ")[1]
    return txt


def remove_indian_country_code(phone):
    if not phone:
        return ""
    if "+91" in str(phone):
        return phone[3::]
    return phone


def separate_name(full_name):
    # Split the full name into words
    if not full_name:
        return " "
    name_parts = full_name.split()

    # Determine the number of name parts
    num_parts = len(name_parts)

    if num_parts == 1:
        # If only one word is provided, consider it as the first name
        first_name = name_parts[0]
        middle_name = ""
        last_name = ""
    elif num_parts == 2:
        # If two words are provided, consider the first as first name and the second as last name
        first_name = name_parts[0]
        middle_name = ""
        last_name = name_parts[1]
    else:
        # If more than two words are provided, consider the first as first name,
        # the last as last name, and everything in between as middle name(s)
        first_name = name_parts[0]
        last_name = name_parts[-1]
        middle_name = " ".join(name_parts[1:-1])

    return {
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
    }


def is_dob_in_range(lead_application, program_doc):
    start = program_doc.get("custom_date_start")
    end = program_doc.get("custom_date_end")
    dob = lead_application.get("date_of_birth")

    if not dob:
        raise frappe.exceptions.MandatoryError("Date of Birth is required")
    if not start or not end:
        return True
    if start <= dob <= end:
        return True
    else:
        return False


@frappe.whitelist()
def create_student_application(**args):
    try:
        if not args:
            raise frappe.exceptions.MandatoryError("Arguments are required")

        lead_doc_name = args.get("name")
        lead_application = frappe.get_doc("Lead", {"name": lead_doc_name})
        program_doc = frappe.get_doc("Program", lead_application.get("class"))

        if not is_dob_in_range(lead_application, program_doc):
            message = f"Date of Birth for class {lead_application.get('class')} is not in range {program_doc.get('custom_date_start')} to {program_doc.get('custom_date_end')}"
            # frappe.msgprint(msg=message, title="Error", indicator="red")
            raise frappe.exceptions.MandatoryError(message)

        if not lead_application:
            return None

        student_application = frappe.get_doc(
            serialize_lead_to_application(lead_application)
        )

        created_mgr_lead = upload_to_mgr(student_application)
        student_application.lms_id = created_mgr_lead.get("ID")
        # lead_application.lead_status = "Enrolled"
        lead_application.status = "Enrolled"
        lead_application.save()
        student_application.insert()
        frappe.msgprint(("Upload to MGR successful"))
        return student_application

    except Exception as e:
        frappe.msgprint(msg=str(e), title="Error", indicator="red")
        raise e


@frappe.whitelist(allow_guest=True)
def update_stud_data(**data):
    data = data.get("Student").get("StudentInfoChange")

    existing_student_doc = frappe.get_list(
        "Student Applicant",
        {"lms_id": data.get("lms_id"), "school": data.get("school_name")},
        ignore_permissions=True,
    )

    if not existing_student_doc or len(existing_student_doc) == 0:
        raise Exception("Student Doesnt exist")
    name = existing_student_doc[0].get("name")

    current_user = frappe.session.user

    frappe.set_user("Administrator")

    adhar_card_cert = save_file(
        str(uuid.uuid4()),
        data.get("adhar_card_cert"),
        "Student Applicant",
        name,
        decode=True,
    )
    image = save_file(
        str(uuid.uuid4()),
        data.get("student_photo"),
        "Student Applicant",
        name,
        decode=True,
    )
    birth_cert = save_file(
        str(uuid.uuid4()),
        data.get("birth_cert"),
        "Student Applicant",
        name,
        decode=True,
    )
    frappe.set_user(current_user)

    existing_student_doc = frappe.get_doc("Student Applicant", {"name": name})

    father_in_doc = next(
        (
            item
            for item in existing_student_doc.get("guardians")
            if item.get("relation") == "Father"
        ),
        {},
    )
    mother_in_doc = next(
        (
            item
            for item in existing_student_doc.get("guardians")
            if item.get("relation") == "Mother"
        ),
        {},
    )
    other_in_doc = next(
        (
            item
            for item in existing_student_doc.get("guardians")
            if item.get("relation") == "Others"
        ),
        {},
    )
    father = frappe.get_doc({"doctype": "Guardian"})
    if father_in_doc:
        father = frappe.get_doc("Guardian", father_in_doc.get("guardian"))
    # father =frappe.get_doc({"doctype":'Guardian',"name":father_in_doc.get('guardian')})
    father.first_name = (data.get("father_f_name"),)
    father.guardian_name = data.get("father_f_name")
    father.middle_name = data.get("father_m_name")
    father.last_name = data.get("father_l_name")
    father.education = data.get("father_education")
    father.occupation = (
        data.get("father_profession") or data.get("father_profession_other") or ""
    )
    father.mobile_number = data.get("father_mobile_no")
    father.annual_income = data.get("father_annual_income")
    father.email_address = data.get("father_email_id")
    father.company_name = data.get("father_company_name")
    father.designation = data.get("father_designation")
    father.work_address = data.get("father_office_address")
    father_in_doc = bool(father_in_doc)

    if not father_in_doc:
        father = father.insert(ignore_permissions=True)
    else:
        father.save(ignore_permissions=True)

    # mother =frappe.get_doc({"doctype":'Guardian',"name":mother_in_doc.get('guardian')})
    mother = frappe.get_doc({"doctype": "Guardian"})
    if mother_in_doc:
        mother = frappe.get_doc("Guardian", mother_in_doc.get("guardian"))
    mother.first_name = data.get("mother_f_name")
    mother.middle_name = data.get("mother_m_name")
    mother.guardian_name = data.get("mother_f_name")
    mother.last_name = data.get("mother_l_name")
    mother.education = (data.get("mother_education"),)
    mother.occupation = (
        data.get("mother_profession") or data.get("mother_profession_other") or ""
    )
    mother.email_address = data.get("mother_email_id")
    mother.mobile_number = data.get("mother_mobile_no")
    mother.annual_income = data.get("mother_annual_income")
    mother.company_name = data.get("mother_company_name")
    mother.designation = data.get("mother_designation")
    mother.work_address = data.get("mother_office_address")

    mother_in_doc = bool(mother_in_doc)

    if not mother_in_doc:
        mother = mother.insert(ignore_permissions=True)
    else:
        mother.save(ignore_permissions=True)

    # other = frappe.get_doc({"doctype":'Guardian',"name":other_in_doc.get('guardian')})
    other = frappe.get_doc({"doctype": "Guardian"})
    if other_in_doc:
        other = frappe.get_doc("Guardian", other_in_doc.get("guardian"))
    other.first_name = data.get("guardian_f_name")
    other.guardian_name = data.get("guardian_f_name") or "not picked"
    other.middle_name = data.get("guardian_m_name")
    other.last_name = data.get("guardian_l_name")
    other.education = data.get("guardian_education")
    other.occupation = (
        data.get("other_profession") or data.get("other_profession_other") or ""
    )
    other.mobile_number = data.get("guardian_mobile_no") or ""
    other.address_line_1 = (data.get("guardian_bld_house"),)
    other.address_line_2 = (data.get("guardian_sub_area"),)
    other.city = (data.get("guardian_city"),)
    other.pincode = (data.get("guardian_pin"),)
    other.day_care_contact = data.get("day_care_contact")
    other_in_doc = bool(other_in_doc)

    if not other_in_doc and data.get("guardian_f_name"):
        other = other.insert(ignore_permissions=True)

    else:
        other.save(ignore_permissions=True)

    if not mother_in_doc:
        existing_student_doc.append(
            "guardians",
            {
                "guardian": mother.get("name"),
                "guardian_name": mother.get("guardian_name"),
                "relation": "Mother",
            },
        )

    if not father_in_doc:
        existing_student_doc.append(
            "guardians",
            {
                "guardian": father.get("name"),
                "guardian_name": father.get("guardian_name"),
                "relation": "Father",
            },
        )

    if not other_in_doc and data.get("guardian_f_name"):
        existing_student_doc.append(
            "guardians",
            {
                "guardian": other.get("name"),
                "guardian_name": other.get("guardian_name"),
                "relation": "Others",
            },
        )

    existing_student_doc.lms_status = data.get("lms_status")

    existing_student_doc.first_name = data.get("stud_f_name")
    existing_student_doc.last_name = data.get("stud_l_name")

    existing_student_doc.gender = data.get("gender")
    existing_student_doc.date_of_birth = data.get("b_date")
    existing_student_doc.address_line_1 = data.get("bld_house")
    existing_student_doc.address_line_2 = data.get("sub_area")
    existing_student_doc.landmark = data.get("landmark")
    existing_student_doc.pincode = data.get("pin")
    existing_student_doc.city = data.get("city")
    existing_student_doc.state = data.get("state")
    existing_student_doc.country = data.get("country")
    existing_student_doc.bus_service_required = data.get("bus_service_required")
    existing_student_doc.admission_to = data.get("admission_to")
    existing_student_doc.academic_year = data.get("academic_year")
    existing_student_doc.stud_rte = data.get("stud_rte")
    existing_student_doc.caste = data.get("other_caste") or data.get("caste")
    existing_student_doc.religion = data.get("other_religion") or data.get("religion")
    existing_student_doc.subcaste = data.get("other_subcaste") or data.get("subcaste")
    existing_student_doc.student_mobile_number = data.get("student_sms_no")
    existing_student_doc.student_is_existingstudent = int(
        data.get("student_isexistingstudent") or 0
    )
    existing_student_doc.student_existing_ref_number = data.get(
        "student_existing_ref_number"
    )
    existing_student_doc.is_sibling_in_school = int(
        data.get("student_bro_sis_inschool") or 0
    )
    existing_student_doc.school = data.get("school_name")
    existing_student_doc.blood_group = data.get("blood_group")
    existing_student_doc.catering = data.get("catering")
    existing_student_doc.aadhaar_card_number = data.get("adhar_card_no")

    existing_student_doc.nationality = data.get("nationality")
    existing_student_doc.allergies = bool(
        data.get("other_allergies") or data.get("allergies")
    )
    existing_student_doc.custom_allergies = data.get("other_allergies") or data.get(
        "allergies"
    )

    existing_student_doc.aadhaar_card_cert = adhar_card_cert.file_url
    existing_student_doc.birth_cert = birth_cert.file_url
    existing_student_doc.image = image.file_url

    existing_student_doc.save(ignore_permissions=True)
    # if(mother_in_doc):
    #     mother.save(ignore_permissions=True)
    # if(father_in_doc):
    #     father.save(ignore_permissions=True)
    # if(other_in_doc):
    #     other.save(ignore_permissions=True)

    return existing_student_doc


def default(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()


def upload_to_mgr(doc):
    program = frappe.db.get_value("Program", doc.get("program"), "program_name") or " "
    JSON = {
        "user": frappe.db.get_single_value("MGR Settings", "username"),
        "password": frappe.utils.password.get_decrypted_password(
            "MGR Settings", "MGR Settings", "password"
        ),
        "school_name": doc.get("school"),
        "first_name": doc.get("first_name") + " " + (doc.get("middle_name") or ""),
        "last_name": doc.get("last_name") or " ",
        "mother_name": doc.get("mother_f_name") or " ",
        "father_name": doc.get("father_f_name"),
        "father_mobile_number": remove_indian_country_code(doc.get("father_mobile_no")),
        "father_email_address": doc.get("father_email"),
        "gender": doc.get("gender") or " ",
        "date_of_birth": doc.get("date_of_birth") or " ",
        "address1": doc.get("address_line_1") or " ",
        "address2": doc.get("address_line_2") or " ",
        "pin": doc.get("pincode") or " ",
        "city": doc.get("city") or " ",
        "state": doc.get("state") or " ",
        "bus_service_required": "yes" if doc.get("bus_service_required") else "no",
        "class": program or " ",
        "RTE_student": "yes" if doc.get("rte_student") else "no",
        "preferred_batch_time": doc.get("batch_time") or " ",
        "academic_year": doc.get("academic_year") or " ",
    }

    response = requests.post(
        url=f'{CONFIG.get("MGR_API_BASE")}/student_lms/post_student_lms_data',
        json=json.loads(json.dumps(JSON, default=default)),
    )
    try:
        if "OK" not in response.text:
            message = json.loads(response.text)
            frappe.msgprint(msg=message.get("message"), title="Error", indicator="red")
            raise frappe.exceptions.DuplicateEntryError(response.text)

        return json.loads(response.text)

    except Exception:
        frappe.log_error("MGR Error", response.text)
        raise frappe.exceptions.DuplicateEntryError(response.text)


def serialize_lead_to_application(doc: dict):
    if not doc:
        return {}

    if not doc.get("fathers_name") or not doc.get("fathers_phone"):
        frappe.msgprint(
            msg="Fathers name/phone is required", title="Error", indicator="red"
        )
        raise frappe.exceptions.MandatoryError("Fathers name/phone is required")

    fees_structure = frappe.db.get_value(
        "Fee Structure",
        {
            "program": doc.get("class"),
            "school": doc.get("center"),
            "academic_year": doc.get("academic_year"),
        },
        "name",
    )
    fathers_name = separate_name(doc.get("fathers_name"))
    father = frappe.get_doc(
        {
            "doctype": "Guardian",
            "guardian_name": doc.get("fathers_name"),
            "first_name": fathers_name.get("first_name") or " ",
            "middle_name": fathers_name.get("middle_name"),
            "last_name": fathers_name.get("last_name"),
            "mobile_number": doc.get("fathers_phone"),
            "email_address": doc.get("fathers_email"),
        }
    ).insert(ignore_permissions=True)
    guardians = [
        {
            "guardian": father.get("name"),
            "relation": "Father",
            "guardian_name": father.get("guardian_name"),
        }
    ]

    if doc.get("mothers_name") and doc.get("mothers_name").strip():
        mothers_name = separate_name(doc.get("mothers_name"))
        mother = frappe.get_doc(
            {
                "doctype": "Guardian",
                "guardian_name": doc.get("mothers_name") or " ",
                "first_name": mothers_name.get("first_name") or " ",
                "middle_name": mothers_name.get("middle_name"),
                "last_name": mothers_name.get("last_name"),
                "mobile_number": doc.get("mothers_phone") or " ",
                "email_address": doc.get("mothers_email"),
            }
        ).insert(ignore_permissions=True)
        guardians.append(
            {
                "guardian": mother.get("name"),
                "relation": "Mother",
                "guardian_name": mother.get("guardian_name"),
            }
        )

    siblings = []
    if doc.get("is_sibling_already_at_walnut"):
        sibling_id = doc.get("custom_if_yes_reference_number_of_child")
        siblings = [{"student": sibling_id}] or []

    return {
        "doctype": "Student Applicant",
        "first_name": doc.get("first_name"),
        "last_name": doc.get("last_name"),
        "school": doc.get("center"),
        "academic_year": doc.get("academic_year"),
        "fee_structure": fees_structure,
        "student_email_id": f"test_only{str(time.time())}@yopmail.com",
        "guardians": guardians,
        "program": doc.get("class"),
        "father_f_name": doc.get("fathers_name"),
        "preferred_batch_time": doc.get("preferred_batch_time"),
        "batch_time": doc.get("preferred_batch_time"),
        "gender": doc.get("gender"),
        "address_line_2": doc.get("address2"),
        "address_line_1": doc.get("address"),
        "country": doc.get("country"),
        "pincode": doc.get("pincode"),
        "state": doc.get("state"),
        "city": doc.get("city"),
        "last_name": doc.get("last_name"),
        "mother_f_name": doc.get("mothers_name"),
        "date_of_birth": doc.get("date_of_birth"),
        "father_email": doc.get("fathers_email"),
        "mother_mobile_number": doc.get("mothers_phone"),
        "father_mobile_no": doc.get("fathers_phone"),
        "bus_service_required": doc.get("bus_service_required"),
        "is_sibling_in_school": doc.get("is_sibling_already_at_walnut"),
        "rte_student": doc.get("stud_rte"),
        "stud_rte": doc.get("rte_student"),
        "catering": doc.get("catering"),
        "siblings": siblings or [],
        "custom_referred_to": doc.get("referred_to"),
        "seeking_admission_in_class": doc.get("class"),
        "if_yes_reference_number_of_child": doc.get("if_yes_reference_number_of_child"),
    }


# 46 Fursungi
# 47 Shivane
# 74 Wakad

#  these ids coresspond to ids on wordpress location, select


id_to_location_map_fb = {
    "wakad": "Wakad",
    "shivane": "Shivane",
    "fursungi": "Fursungi",
    "walnut school at shivane": "Shivane",
    "walnut school at fursungi": "Fursungi",
}


@frappe.whitelist(allow_guest=True)
def create_student_lead(**kwargs):
    # return kwargs
    if (
        not kwargs.get("first_name")
        or not kwargs.get("fathers_name")
        or not kwargs.get("fathers_phone")
    ):
        raise frappe.exceptions.MandatoryError(
            "First Name , Fathers Name or Fathers phone is required"
        )
    student_name = separate_name(kwargs.get("first_name"))
    existing_leads = frappe.db.get_list(
        "Lead",
        filters={
            "first_name": student_name.get("first_name"),
            "fathers_name": kwargs.get("fathers_name"),
            "fathers_phone": remove_indian_country_code(
                str(kwargs.get("fathers_phone"))
            ),
        },
        ignore_permissions=True,
    )
    if len(existing_leads):
        return process_lead(
            kwargs.get("source"), frappe.get_doc("Lead", existing_leads[0].get("name"))
        )

    school_name = (
        frappe.db.get_value(
            "School",
            {"location": id_to_location_map_fb.get(str(kwargs.get("school")).lower())},
            "name",
        )
        or kwargs.get("school")
        or kwargs.get("school")
    )

    class_name = (
        frappe.db.get_value(
            "Program",
            {
                "school": school_name,
                "program_name": get_class_without_std(str(kwargs.get("class"))),
            },
            "name",
        )
        or kwargs.get("class")
        or kwargs.get("class")
    )

    lead_doc = frappe.get_doc(
        {
            "doctype": "Lead",
            "first_name": student_name.get("first_name"),
            "last_name": student_name.get("last_name"),
            "middle_name": student_name.get("middle_name"),
            "fathers_name": kwargs.get("fathers_name"),
            "fathers_email": kwargs.get("father_email_id")
            or kwargs.get("fathers_email"),
            "fathers_phone": remove_indian_country_code(
                str(kwargs.get("fathers_phone"))
            ),
            # "mobile_no": remove_indian_country_code(str(kwargs.get("fathers_phone"))),
            "mothers_name": " ",
            "academic_year": kwargs.get("academic_year") or "2024-2025",
            "school_from_lead_source": kwargs.get("school"),
            "center": school_name,
            "class": class_name,
            "class_from_lead_source": kwargs.get("class"),
            "custom_previous_school":kwargs.get('current_school',''),
            "source": kwargs.get("source", "Website") or "Website" or "Others",
        }
    )

    lead_doc = lead_doc.insert(ignore_permissions=True)
    return lead_doc


# to remove
@frappe.whitelist(allow_guest=True)
def create_student_lead_fb(**kwargs):
    # return kwargs
    if (
        not kwargs.get("first_name")
        or not kwargs.get("fathers_name")
        or not kwargs.get("fathers_phone")
    ):
        raise frappe.exceptions.MandatoryError(
            "First Name , Fathers Name or Fathers phone is required"
        )
    student_name = separate_name(kwargs.get("first_name"))
    existing_leads = frappe.db.get_list(
        "Lead",
        filters={
            "first_name": student_name.get("first_name"),
            "fathers_name": kwargs.get("fathers_name"),
            "fathers_phone": remove_indian_country_code(kwargs.get("fathers_phone")),
        },
        ignore_permissions=True,
    )
    if len(existing_leads):
        return process_lead(
            kwargs.get("source"), frappe.get_doc("Lead", existing_leads[0].get("name"))
        )

    school_name = (
        frappe.db.get_value(
            "School",
            {"location": id_to_location_map_fb.get(str(kwargs.get("school")).lower())},
            "name",
        )
        or kwargs.get("school")
        or kwargs.get("school")
    )

    class_name = (
        frappe.db.get_value(
            "Program",
            {
                "school": school_name,
                "program_name": get_class_without_std(str(kwargs.get("class"))),
            },
            "name",
        )
        or kwargs.get("class")
        or kwargs.get("class")
    )

    lead_doc = frappe.get_doc(
        {
            "doctype": "Lead",
            "first_name": student_name.get("first_name"),
            "last_name": student_name.get("last_name"),
            "middle_name": student_name.get("middle_name"),
            "fathers_name": kwargs.get("fathers_name"),
            "fathers_email": kwargs.get("father_email_id")
            or kwargs.get("fathers_email"),
            "fathers_phone": remove_indian_country_code(kwargs.get("fathers_phone")),
            "mothers_name": " ",
            "academic_year": kwargs.get("academic_year") or "2024-2025",
            "school_from_lead_source": kwargs.get("school"),
            "center": school_name,
            "class": class_name,
            "class_from_lead_source": kwargs.get("class"),            
            "custom_previous_school":kwargs.get('current_school',''),
            "source": kwargs.get("source") or "Facebook",
        }
    )

    lead_doc = lead_doc.insert(ignore_permissions=True)
    return lead_doc


def process_lead(source, lead):
    lead.status = "Hot"
    if source.lower() == "school":
        lead.append("custom_lead_sub_status", {"sub_status": "Hot-School Visit Done"})
        lead.custom_walk_in_1_action_date = datetime.datetime.now(
            pytz.timezone("Asia/Kolkata")
        ).strftime("%Y-%m-%d")

    lead.append(
        "notes",
        {
            "note": f'<div class="ql-editor read-mode"><p>Lead Re-Registered from <b>{source.capitalize()}</b> at <b>{datetime.datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y , %H:%M IST")}</b> </p></div>'
        },
    )

    lead.save(ignore_permissions=True)
    return lead
