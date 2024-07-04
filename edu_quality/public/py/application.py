import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from edu_quality.public.py.discount import (
    calculate_discount,
    get_discount_list,
    update_component,
    update_payment_plan_after_discount,
)
from edu_quality.edu_quality.server_scripts.student_applicant import (
    add_referral_discount,
)
from edu_quality.api.google_admin import create_google_user

from edu_quality.edu_quality.server_scripts.utils import (
    is_rolled_over,
    get_previous_class,
    previous_academic_year,
)
from edu_quality.public.py.student import update_student


def autoname(doc, method=None):
    if doc.school_code and doc.class_name:
        school_code = doc.school_code
        class_name = doc.class_name
        naming_format = f"{school_code}-{class_name}-LD-"
        doc.name = make_autoname(naming_format + ".#####")


def before_save(doc, method=None):
    doc.fee_components = []
    doc.application_fees = 0
    if frappe.db.exists("Application Fees List", {"class_name": doc.program}):
        doc.application_fees = frappe.get_value(
            "Application Fees List", {"class_name": doc.program}, "application_fees"
        )
        fee_name = frappe.get_value(
            "Application Fees List", {"class_name": doc.program}, "fee_category"
        )
        if not fee_name:
            fee_name = "Application fee"
        label = frappe.db.get_value("Fee Category",fee_name,"custom_label")
        school = frappe.db.get_value("Fee Category",fee_name,"school")
        company = frappe.db.get_value("Fee Category",fee_name,"custom_company")
        component = {"fees_category": fee_name, "amount": doc.application_fees,"label":label,'school':school,'custom_company':company}

        doc.append(
            "fee_components", component
        )

    if frappe.db.get_single_value("Fees Settings", "apply_deposits"):
        get_deposits(doc)

    if not doc.fee_structure:
        if frappe.db.exists(
            "Fee Structure",
            {
                "program": doc.program,
                "academic_year": doc.academic_year,
                "docstatus": 1,
            },
        ):
            doc.fee_structure = frappe.get_value(
                "Fee Structure",
                {
                    "program": doc.program,
                    "academic_year": doc.academic_year,
                    "docstatus": 1,
                },
                "name",
            )

    if doc.fee_structure:
        fee_schedule = frappe.db.get_value(
            "Fee Schedule", {"fee_structure": doc.fee_structure, "docstatus": 1}, "name"
        )
        doc.fee_schedule = fee_schedule
        doc.application_fees = frappe.db.get_value(
            "Application Fees List", {"class_name": doc.program}, "application_fees"
        )

        fee_structure = frappe.get_doc("Fee Structure", doc.fee_structure)
        if frappe.db.get_single_value("Fees Settings", "apply_fees"):
            for component in fee_structure.components:
                if doc.is_rte and component.rte_excempt:
                    continue
                doc.append(
                    "fee_components",
                    {
                        "fees_category": component.fees_category,
                        "amount": component.amount,
                        "description": component.description,
                        "custom_company": component.custom_company,
                        "school": component.school,
                        "label": component.label
                    },
                )
    calculate_total(doc)


def calculate_total(doc):
    doc.total_amount = 0
    for component in doc.fee_components:
        if component.amount:
            doc.total_amount += float(component.amount)


def get_deposits(doc):
    deposits = frappe.get_all(
        "Security Deposit",
        {"program": doc.program, "academic_year": doc.academic_year},
        ["name", "amount"],
    )
    for deposit in deposits:
        label = frappe.get_value("Fee Category", deposit.name, "custom_label")
        school = frappe.db.get_value("Fee Category",deposit.name,"school")
        company = frappe.db.get_value("Fee Category",deposit.name,"custom_company")
        doc.append(
            "fee_components", {"fees_category": deposit.name, "amount": deposit.amount,'label': label,'school':school,'custom_company':company}
        )


@frappe.whitelist()
def enroll_student(source_name, email=None, refno=None, data=None):
    """Creates a Student Record and returns a Program Enrollment.

    :param source_name: Student Applicant.
    """

    frappe.publish_realtime(
        "enroll_student_progress", {"progress": [1, 4]}, user=frappe.session.user
    )
    student = get_mapped_doc(
        "Student Applicant",
        source_name,
        {
            "Student Applicant": {
                "doctype": "Student",
                "field_map": {"name": "student_applicant"},
            }
        },
        ignore_permissions=True,
    )
    student_applicant = frappe.get_doc("Student Applicant", source_name)
    if student_applicant.custom_referred_by:
        add_referral_discount(student_applicant.custom_referred_by, student_applicant)

    student_group = get_student_group(student_applicant)
    if refno:
        student.reference_number = refno
    if email:
        student.student_email_id = email
    if data:
        student_data = update_student(data)
        student.update(student_data)
    student.save()
    create_student_account(student, student_applicant)
    program_enrollment = frappe.new_doc("Program Enrollment")
    program_enrollment.student = student.name
    program_enrollment.student_category = student_applicant.student_category
    program_enrollment.student_name = student.student_name
    program_enrollment.custom_school = student_applicant.school
    program_enrollment.program = student_applicant.program
    program_enrollment.academic_year = student_applicant.academic_year
    program_enrollment.academic_term = student_applicant.academic_term
    program_enrollment.student_group = student_group
    program_enrollment.save()
    program_enrollment.submit()
    frappe.publish_realtime(
        "enroll_student_progress", {"progress": [2, 4]}, user=frappe.session.user
    )
    return program_enrollment


def get_student_group(doc):
    query = """
            select sg.name,sg.student_group_name,sg.current_count,sg.max_strength from `tabStudent Group` as sg
            where sg.academic_year = %(academic_year)s
            and sg.program = %(program)s
            and sg.batch = %(batch)s
            and sg.current_count<sg.max_strength
            """
    result = frappe.db.sql(query, doc.as_dict(), as_dict=True)
    rolled_over = is_rolled_over(doc.academic_year)
    for i in result:
        if not rolled_over:
            previous_class = get_previous_class(doc.program)
            previous_academic_yr = previous_academic_year(doc.academic_year)
            previous_count = frappe.db.get_value(
                "Student Group",
                {
                    "program": previous_class,
                    "academic_year": previous_academic_yr,
                    "student_group_name": i.student_group_name,
                },
            )
            if previous_count + i.current_count < i.max_strength:
                return i.name
        else:
            if i.current_count < i.max_strength:
                return i.name
    return frappe.throw(
        "No Student Group Available! Please Change the Batch and check again."
    )


def get_max_strength(student_group):
    return frappe.db.get_value("Student Group", student_group, "max_strength")


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
        ).get("primaryEmail", "")

        student.student_email_id = created_email
        student.save()


def find_first_key_with_value(list_of_dicts, key, value):
    for dictionary in list_of_dicts:
        frappe.errprint(dictionary["email_address"])
        if key in dictionary and dictionary[key]:
            return dictionary[key]


def get_student_count(fee_schedule, student_group):
    for sg in fee_schedule.student_groups:
        if sg.student_group == student_group:
            return int(sg.total_students)
    return 0
