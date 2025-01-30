import time

import frappe
from frappe.utils import today

from edu_quality.api.google_admin import suspend_google_user, unsuspend_google_user
from edu_quality.overrides import make_payment_request
from edu_quality.api.google_admin import create_google_user, add_user_to_group


def find_first_key_with_value(list_of_dicts, key, value):
    for dictionary in list_of_dicts:
        frappe.errprint(dictionary["email_address"])
        if key in dictionary and dictionary[key]:
            return dictionary[key]


def get_phone_no_from_guardians(guardians):
    guardians_names = [guardian.get("guardian") for guardian in guardians]
    guardian_data = frappe.db.get_list(
        "Guardian",
        filters=[["name", "in", guardians_names]],
        fields=["mobile_number", "email_address"],
    )
    mobile_number = find_first_key_with_value(guardian_data, "mobile_number", "")
    email_address = find_first_key_with_value(guardian_data, "email_address", "")
    return mobile_number, email_address


def create_student_account(student, student_applicant):
    google_service_settings = frappe.get_single("Google Service Account")

    if google_service_settings.get("create_student_workspace"):
        mobile_number, email_address = get_phone_no_from_guardians(
            student_applicant.get("guardians")
        )
        email_key = student.get("name")
        first_name = student_applicant.get("first_name")
        last_name = student_applicant.get("last_name")
        created_email = create_google_user(
            google_service_settings.get("google_account_prefix", "") + email_key,
            first_name,
            last_name,
            email_address,
            mobile_number,
        )
        if created_email:
            created_email=created_email.get("primaryEmail", "")
        else:
            created_email = student.student_email_id

        group_email = frappe.get_value("School", student.school, "group_email")
        if group_email:
            add_user_to_group(created_email, group_email)
        student.save()


def autoname(doc, method=None):
    school_prefixes = {
        "Walnut School at Fursungi": "FU",
        "Walnut School at Shivane": "SH",
        "Walnut School at Wakad": "WA",
    }

    if doc.imported and doc.reference_number:
        prefix = school_prefixes.get(doc.school, "")
        doc_name = prefix + doc.reference_number
        doc.name = doc_name
    elif doc.reference_number:
        prefix = school_prefixes.get(doc.school, "")
        doc_name = prefix + doc.reference_number
        doc.name = doc_name
    elif doc.student_applicant:
        applicant = frappe.get_doc("Student Applicant", doc.student_applicant)
        prefix = frappe.get_value("School", applicant.school, "prefix")
        series = get_reference(doc.program)
        prefix += series
        ref_id = get_last_id(prefix)
        if ref_id == "max":
            prefix = prefix[:2]
            if series[1] != "Z":
                series = series[0] + chr(ord(series[1]) + 1)
            elif series[0] != "Z":
                series = chr(ord(series[0]) + 1) + "A"
            else:
                series = "A" + "A"
            frappe.db.set_value(
                "Program", applicant.program, "reference_series", series
            )
            prefix = prefix + series + "01"
        else:
            prefix = prefix + ref_id
        doc.name = prefix
        doc.student_email_id = doc.name + "@walnutedu.in"
        doc.reference_number = doc.name[2:]
        
        
def get_last_id(prefix):
    val = frappe.db.get_all(
        "Student", [["name", "Like", prefix + "%"]], "name", order_by="name"
    )
    if val:
        series = int(val[-1].name[-2:])
        frappe.logger("series").exception(series)
        if series == 99:
            return "max"
        series += 1
        return str(series) if series > 9 else "0" + str(series)
    else:
        return "01"


def before_insert(doc, method=None):
    frappe.flags.in_import = True


def after_insert(doc, method=None):
    if doc.student_applicant:
        applicant = frappe.get_doc("Student Applicant", doc.student_applicant)
        frappe.log_error("Student after insert called")
        create_student_account(doc, applicant)


def before_save(doc, method=None):
    try:
        prev_doc = doc.get_doc_before_save()
        if prev_doc and prev_doc.student_status != doc.student_status:
            if doc.student_status == "Defaulter":
                suspend_google_user(doc.student_email_id)
            else:
                unsuspend_google_user(doc.student_email_id)
        comment_on_possible_dropout(doc, prev_doc)
    except Exception as e:
        frappe.logger("google_user").exception(e)


def on_update(doc, method=None):
    to_update = {
        "custom_status": doc.student_status,
        "has_allergies": doc.has_allergies,
        "allergies": doc.allergies,
        "is_handicap": doc.is_handicap,
        "handicap": doc.handicap,
    }
    program_enrollment = frappe.get_all(
        "Program Enrollment", {"student": doc.name, "docstatus": ["!=", 2]}, ["name"]
    )
    for pe in program_enrollment:
        frappe.set_value("Program Enrollment", pe.name, to_update)


def comment_on_possible_dropout(doc, old_doc):
    if not old_doc:
        return
    if (not old_doc.possible_dropout) and doc.possible_dropout:
        doc.add_comment("Comment", "Intimation of Possible Dropout!")
    elif (old_doc.possible_dropout) and (not doc.possible_dropout):
        doc.add_comment("Comment", "Intimation of Possible Dropout Cleared!")


def get_reference(program):
    if not frappe.db.get_value(
        "Academic Year",
        [
            ["Academic Year", "year_start_date", "<=", today()],
            ["Academic Year", "year_end_date", ">=", today()],
        ],
        "rolled_over",
    ):
        current_program = frappe.get_doc("Program", program)
        series = frappe.db.get_value(
            "Program",
            {
                "school": current_program.school,
                "sequence": current_program.sequence - 1,
            },
            "reference_series",
        )
        if not series:
            series = current_program.reference_series
            series = chr(ord(series[0]) + 1) + series[1]
    else:
        series = frappe.db.get_value("Program", program, "reference_series")
    return series


def update_student_group(p_e_doc, fee_structure=None):
    try:
        student_group = frappe.get_value(
            "Program Enrollment", {"name": p_e_doc, "docstatus": 1}, "student_group"
        )
        st = get_students_group(student_group)
        if st:
            program_e_d = frappe.get_doc("Student Group", student_group)
            program_e_d.students = []
            for item in st:
                program_e_d.append("students", item)
            program_e_d.save()
            if frappe.db.exists("Fee Schedule", {"fee_structure": fee_structure}):
                fee_schedule = frappe.get_value(
                    "Fee Schedule", {"fee_structure": fee_structure}
                )
                frappe.db.set_value(
                    "Fee Schedule Student Group",
                    {"parent": fee_schedule, "student_group": student_group},
                    "total_students",
                    len(st),
                )
        return
    except Exception as e:
        frappe.throw(str(e))


def get_students_group(student_group):
    enrolled_students = frappe.get_all(
        "Program Enrollment",
        {"student_group": student_group, "docstatus": 1},
        ["student", "student_name"],
    )
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


def create_payment_request(fee, term=None):
    try:
        if not frappe.db.exists(
            "Payment Request",
            {
                "reference_doctype": fee.doctype,
                "reference_docname": fee.name,
                "docstatus": 1,
            },
        ):
            time.sleep(30)
            make_payment_request(
                party_type="Student",
                party=fee.student,
                dt=fee.doctype,
                dn=fee.name,
                payment_term=term,
                recipient_id=frappe.get_value(
                    "Student", fee.student, "student_email_id"
                ),
                submit_doc=True,
                use_dummy_message=True,
            )
    except Exception as e:
        frappe.logger("edu_quality").exception(e)


@frappe.whitelist()
def get_fees_details(student):
    class_id = frappe.get_value(
        "Program Enrollment",
        {"student": student, "docstatus": 1},
        "program",
        order_by="creation desc",
    )
    if class_id and frappe.get_value(
        "Fees", {"student": student, "program": class_id, "docstatus": 1}
    ):
        return frappe.get_doc(
            "Fees", {"student": student, "program": class_id}
        ).payment_schedule
    elif class_id and frappe.get_value(
        "Fee Advance", {"student": student, "program": class_id, "docstatus": 1}
    ):
        doc = frappe.get_doc("Fee Advance", {"student": student, "program": class_id})
        invoice_portion = frappe.get_value(
            "Payment Schedule",
            {"parent": doc.payment_plan, "payment_term": doc.payment_term},
            "invoice_portion",
        )
        return [
            {
                "payment_term": doc.payment_term,
                "payment_amount": doc.amount,
                "due_date": doc.due_date,
                "invoice_portion": invoice_portion,
                "doctype": doc.doctype,
                "parent": doc.name,
                "paid_date": doc.paid_date,
                "description": "Installment 1",
                "outstanding": doc.outstanding_amount,
            }
        ]
    return False


@frappe.whitelist()
def get_parents_details(student):
    student = frappe.get_doc("Student", student)
    parents = []
    for guardian in student.guardians:
        parent = frappe.get_doc("Guardian", guardian.guardian).as_dict()
        parent.update({"relation": guardian.relation})
        parents.append(parent)
    return parents


def update_student(data):
    student_meta = data.get("student_meta")
    parent_meta = data.get("parent_meta", {})
    student_data = {
        "enabled": 1,
        # "form_id": student_meta.get("form_id"),
        "form_code": student_meta.get("form_code"),
        "first_name": student_meta.get("first_name"),
        "middle_name": student_meta.get("middle_name"),
        "last_name": student_meta.get("last_name"),
        # "first_name_marathi": student_meta.get("fname_marathi"),
        # "last_name_marathi": student_meta.get("lname_marathi"),
        "date_of_birth": student_meta.get("b_date"),
        "blood_group": student_meta.get("blood_group", ""),
        "student_mobile_number": student_meta.get("student_primary_contact_number"),
        "gender": student_meta.get("gender"),
        "nationality": student_meta.get("nationality"),
        "address_line_1": student_meta.get("bld_house"),
        "pincode": student_meta.get("pin"),
        "city": student_meta.get("city"),
        "state": student_meta.get("state"),
        "landmark": student_meta.get("landmark"),
        "aadhaar_card_number": student_meta.get("adhar_card_no"),
        "category": student_meta.get("category"),
        "catering": student_meta.get("catering"),
        "caste": student_meta.get("caste"),
        "other_caste": student_meta.get("other_caste"),
        "sub_caste": student_meta.get("subcaste"),
        "other_sub_caste": student_meta.get("other_subcaste"),
        "mother_tongue": student_meta.get("mother_tongue"),
        "is_existing_student": student_meta.get("student_isexistingstudent"),
        "existing_student_ref_number": student_meta.get("student_existing_ref_number"),
        "is_handicap": 1 if student_meta.get("handicap") else 0,
        "handicap": student_meta.get("handicap"),
        "is_student_disabled": 1 if student_meta.get("student_isdisability") else 0,
        "student_disability_name": student_meta.get("student_disability_name"),
        "is_sibling_in_school": student_meta.get("student_bro_sis_inschool"),
        "is_rte": student_meta.get("stud_rte"),
        "single_parent_reason": student_meta.get("single_parent_reason"),
        "religion": student_meta.get("religion"),
        "has_allergies": 1 if student_meta.get("allergies") else 0,
        "allergies": student_meta.get("allergies"),
        "parent_divorced": student_meta.get("if_divorced"),
        "student_status": map_student_status(student_meta.get("status")),
        "birth_place": student_meta.get("birthplace"),
        "last_school_attended": student_meta.get("student_last_school_name"),
        "bus_service_required": student_meta.get("bus_service_required"),
        "source_name": student_meta.get("ref_source_name"),
        "guardians": get_guardian(parent_meta),
        "whatsapp_number": student_meta.get("student_sms_no"),
        "primary_contact": student_meta.get("student_emergency_contact_no"),
    }

    return student_data


def map_student_status(status):
    status = status.lower()
    student_statuses = {
        "new": "New student",
        "current": "Current student",
        "cancelled": "Cancelled",
        "not attending": "Not attending",
        "defaulter": "Defaulter",
        "alumni": "Alumni",
    }
    return student_statuses.get(status, "Unknown status")


def get_guardian(data):
    try:
        attributes_mapping = {
            "Father": {
                "attributes": [
                    "f_name",
                    "m_name",
                    "s_name",
                    "email_id",
                    "mobile_no",
                    "education",
                    "profession",
                    "annual_income",
                    "office_address",
                    "company_name",
                    "designation",
                ],
                "function": create_guardian,
            },
            "Mother": {
                "attributes": [
                    "f_name",
                    "m_name",
                    "s_name",
                    "email_id",
                    "mobile_no",
                    "education",
                    "profession",
                    "annual_income",
                    "office_address",
                    "company_name",
                    "designation",
                ],
                "function": create_guardian,
            },
        }

        guardians = []
        for relation, config in attributes_mapping.items():
            kwargs = {
                attr: data.get(f"{relation.lower()}_{attr}")
                for attr in config["attributes"]
            }
            guardian = config["function"](relation, **kwargs)
            if guardian:
                guardians.append(guardian)
        return guardians
    except Exception as e:
        frappe.logger("enrollment").exception(e)


def create_guardian(relation, **kwargs):
    try:
        if not kwargs.get("f_name", ""):
            return None
        first_name = kwargs.get("f_name", "").capitalize()
        frappe.logger("enrollment").exception(first_name)
        middle_name = (
            kwargs.get("m_name", "").capitalize() if kwargs.get("m_name") else None
        )
        last_name = (
            kwargs.get("s_name", "").capitalize() if kwargs.get("s_name") else None
        )
        guardian_name = f"{first_name} {last_name or ''}"
        mobile_no = kwargs.get("mobile_no")
        email_id = kwargs.get("email_id").lower() if kwargs.get("email_id") else None
        guardian_field = "father" if relation == "Father" else "mother"
        guardian = frappe.get_value(
            "Guardian", {f"guardian_name": guardian_name, "mobile_number": mobile_no}
        )
        if not first_name:
            return None
        if not guardian:
            doc = {
                "doctype": "Guardian",
                "guardian_name": guardian_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "last_name": last_name,
                "mobile_number": mobile_no,
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
    except Exception as e:
        frappe.logger("enrollment").exception(e)
