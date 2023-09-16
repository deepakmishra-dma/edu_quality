import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname


def autoname(doc,method=None):
    if doc.school_code and doc.class_name:
        school_code = doc.school_code
        class_name = doc.class_name
        naming_format = f"{school_code}-{class_name}-LD-"
        doc.name = make_autoname(naming_format + ".#####")

def before_save(doc,method=None):
    doc.fee_components = []
    doc.application_fees = 0
    if frappe.db.exists("Application Fees List",{'class_name':doc.program}):
        doc.application_fees = frappe.get_value("Application Fees List",{'class_name':doc.program},'application_fees')
        doc.append('fee_components',{
            'fees_category': "Application fee",
            'amount': doc.application_fees
        })
    if frappe.db.get_single_value("Fees Settings",'apply_deposits'):
        get_deposits(doc)
    if not doc.fee_structure:
        if frappe.db.exists("Fee Structure",{'class':doc.program,'academic_year':doc.academic_year}):
            doc.fee_structure = frappe.get_value("Fee Structure",{'class':doc.program,'academic_year':doc.academic_year},'name')
    if doc.fee_structure:
        fee_structure = frappe.get_doc("Fee Structure", doc.fee_structure)
        if frappe.db.get_single_value("Fees Settings",'apply_fees'):
            for component in fee_structure.components:
                doc.append('fee_components',{
                    'fees_category':component.fees_category,
                    'amount':component.amount,
                    'description': component.description
                    })
    calculate_total(doc)

def calculate_total(doc):
    doc.total_amount = 0
    for component in doc.fee_components:
        if component.amount:
            doc.total_amount += float(component.amount)

def get_deposits(doc):
    deposits = frappe.get_all('Security Deposit',{'program':doc.program,'academic_year':doc.academic_year},['name','amount'])
    for deposit in deposits:
        doc.append('fee_components',{
            'fees_category': "Deposit",
            'amount': deposit.amount
        })
    

@frappe.whitelist()
def enroll_student(source_name):
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

    # student.school = student_applicant.school
    # student.custom_first_name_of_child = student_applicant.first_name_of_child
    # student.custom_fathers_name = student_applicant.fathers_name
    # student.custom_lms_refno = student_applicant.lms_refno
    # student.custom_lms_status = student_applicant.lms_status
    # student.custom_lms_id = student_applicant.lms_id
    # student.custom_referred_by = student_applicant.custom_referred_by
    # student.custom_referrer_school = student_applicant.custom_referrer_school
    # student.custom_aadhaar_card_number = student_applicant.aadhaar_card_number
    # student.custom_seeking_admission_in_class = student_applicant.seeking_admission_in_class
    # student.custom_religion = student_applicant.religion
    # student.custom_caste = student_applicant.caste
    # student.custom_subcaste = student_applicant.subcaste
    # student.custom_category = student_applicant.category
    # student.custom_allergies = student_applicant.allergies
    # student.custom_handicap = student_applicant.handicap
    # student.custom_is_student_disabled = student_applicant.student_is_disabled
    # student.custom_student_disability_name = student_applicant.student_disablity_name
    # student.custom_birth_certificate = student_applicant.birth_cert
    # student.custom_batch_time = student_applicant.batch_time
    # student.custom_student_referral_number = student_applicant.student_refferal_refno
    # student.custom_is_existing_student = student_applicant.student_is_existingstudent
    # student.custom_existing_student_ref_number = student_applicant.student_existing_ref_number
    # student.custom_student_photo = student_applicant.student_photo
    # student.custom_aadhaar_card_certificate = student_applicant.aadhar_card_cert
    # student.custom_parent_status = student_applicant.parent_status 
    # student.custom_single_parent_reason = student_applicant.single_parent_reason
    # student.custom_if_divorced = student_applicant.if_divorced
    # student.custom_bus_service_required = student_applicant.bus_service_required
    # student.custom_is_rte_student = student_applicant.stud_rte
    # student.custom_catering = student_applicant.catering
    # student.custom_admission_to = student_applicant.admission_to
    # student.custom_division = student_applicant.division

    # student.custom_landmark = student_applicant.landmark

    # # Father's Details
    # student.custom_fathers_first_name = student_applicant.father_f_name
    # student.custom_fathers_middle_name = student_applicant.father_m_name
    # student.custom_fathers_last_name = student_applicant.father_l_name
    # student.custom_fathers_mobile_no = student_applicant.father_mobile_no
    # student.custom_fathers_email = student_applicant.father_email
    # student.custom_fathers_education = student_applicant.father_education
    # student.custom_fathers_profession = student_applicant.father_profession
    # student.custom_fathers_annual_income = student_applicant.father_annual_income
    # student.custom_fathers_company_name = student_applicant.father_company_name
    # student.custom_fathers_designation = student_applicant.father_designation
    # student.custom_fathers_office_addres = student_applicant.father_office_addres

    # # Mother's Details
    # student.custom_mothers_first_name = student_applicant.mother_f_name
    # student.custom_mothers_middle_name = student_applicant.mother_m_name
    # student.custom_mothers_last_name = student_applicant.mother_l_name
    # student.custom_mothers_mobile_no = student_applicant.mother_mobile_number
    # student.custom_mothers_email = student_applicant.mother_email_id
    # student.custom_mothers_education = student_applicant.mother_education
    # student.custom_mothers_profession = student_applicant.mother_profession
    # student.custom_mothers_annual_income = student_applicant.mother_annual_income
    # student.custom_mothers_company_name = student_applicant.mother_company_name
    # student.custom_mothers_designation = student_applicant.mother_designation
    # student.custom_mothers_office_address = student_applicant.mother_office_address


    # # Guardian's Details
    # student.custom_guardians_first_name = student_applicant.guardian_f_name
    # student.custom_guardians_middle_name = student_applicant.guardian_m_name
    # student.custom_guardians_last_name = student_applicant.guardian_l_name
    # student.custom_guardians_mobile_no = student_applicant.guardian_mobile_no
    # student.custom_guardians_email_id = student_applicant.guardian_email_id
    # student.custom_guardians_profession = student_applicant.guardian_profession
    # student.custom_guardians_profession_other = student_applicant.guardian_profession_other
    # student.custom_guardians_address_1 = student_applicant.guardian_address1
    # student.custom_guardians_address_2 = student_applicant.guardian_address2
    # student.custom_guardians_city = student_applicant.guardian_city
    # student.custom_guardians_pin = student_applicant.guardian_pin
    # student.custom_day_care_contact = student_applicant.day_care_contact

    # student.custom_is_sibling_in_school = student_applicant.is_sibling_in_school

    student.save()


    program_enrollment = frappe.new_doc("Program Enrollment")
    program_enrollment.student = student.name
    program_enrollment.student_category = student_applicant.student_category
    program_enrollment.student_name = student.student_name
    program_enrollment.school = student_applicant.program
    program_enrollment.program = student_applicant.program
    program_enrollment.academic_year = student_applicant.academic_year
    program_enrollment.academic_term = student_applicant.academic_term
    program_enrollment.student_group = get_student_group(student_applicant)
    program_enrollment.save()
    program_enrollment.submit()
    frappe.publish_realtime(
    	"enroll_student_progress", {"progress": [2, 4]}, user=frappe.session.user
    )
    return program_enrollment

def get_student_group(doc):
    filters = {"academic_year": doc.academic_year, "program": doc.program}
    return frappe.db.get_value("Student Group", filters, "name")