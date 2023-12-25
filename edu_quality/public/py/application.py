import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from edu_quality.public.py.discount import (
    calculate_discount,
    get_discount_list,
    update_component,
    update_payment_plan_after_discount,
)

try:
    from nextai.funnel.custom_trigger import trigger_event
except ImportError:
    print("Chatnext is not installed")

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
        fee_name = frappe.get_value("Application Fees List",{'class_name':doc.program},'fee_category')
        if not fee_name:
            fee_name = "Application fee"
        doc.append('fee_components',{
            'fees_category': fee_name,
            'amount': doc.application_fees
        })
        
    if frappe.db.get_single_value("Fees Settings",'apply_deposits'):
        get_deposits(doc)

    if not doc.fee_structure:
        if frappe.db.exists("Fee Structure",{'program':doc.program,'academic_year':doc.academic_year}):
            doc.fee_structure = frappe.get_value("Fee Structure",{'program':doc.program,'academic_year':doc.academic_year},'name')

    if doc.fee_structure:
        fee_schedule = frappe.db.get_value("Fee Schedule",{'fee_structure':doc.fee_structure},'name')
        doc.fee_schedule = fee_schedule
        doc.application_fees = frappe.db.get_value("Application Fees List",{'class_name':doc.program},'application_fees')

        fee_structure = frappe.get_doc("Fee Structure", doc.fee_structure)
        if frappe.db.get_single_value("Fees Settings",'apply_fees'):
            for component in fee_structure.components:
                if doc.is_rte and component.rte_excempt:
                    continue
                doc.append('fee_components',{
                    'fees_category':component.fees_category,
                    'amount':component.amount,
                    'description': component.description
                })
    calculate_total(doc)


def after_insert(doc, method=None):
    referred_by = doc.custom_referred_by
    add_referral_discount(referred_by)


def calculate_total(doc):
    doc.total_amount = 0
    for component in doc.fee_components:
        if component.amount:
            doc.total_amount += float(component.amount)

def get_deposits(doc):
    deposits = frappe.get_all('Security Deposit',{'program':doc.program,'academic_year':doc.academic_year},['name','amount'])
    for deposit in deposits:
        doc.append('fee_components',{
            'fees_category': deposit.name,
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
    fee_schedule = frappe.get_doc("Fee Schedule", student_applicant.fee_schedule)
    student_group = get_student_group(student_applicant)
    student_count = get_student_count(fee_schedule, student_group)
    max_strength = get_max_strength(student_group)
    if student_count >= max_strength and max_strength != 0:
        frappe.throw(
            title="Division Full",
            msg="Division {0} has reached maximum strength".format(student_group),
        )

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
    program_enrollment.school = student_applicant.school
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
    filters = {"academic_year": doc.academic_year, "program": doc.program}
    return frappe.db.get_value("Student Group", filters, "name")


def get_max_strength(student_group):
    return frappe.db.get_value("Student Group", student_group, "max_strength")


def get_student_count(fee_schedule, student_group): 
    for sg in fee_schedule.student_groups:
        if sg.student_group == student_group:
            return int(sg.total_students)
    return 0
    

def add_referral_discount(referred_by):
    try:
        student_email_id = frappe.get_value("Student", referred_by, "student_email_id")
        referral_settings = frappe.get_single("Referral Settings")
        referral_amounts = {r.get('idx'): r.get('referral_amount') for r in referral_settings.referral}
        ref_doc_name = frappe.get_value("Referral Log", {"student_id": referred_by}, "name")

        if ref_doc_name:
            ref_doc = frappe.get_doc("Referral Log", ref_doc_name)
            previous_referral_amount = float(ref_doc.referral_amount)
            referral_no = int(ref_doc.number_of_referral) + 1
            ref_doc.number_of_referral = referral_no
            amount = referral_amounts.get(referral_no)

            if amount:
                ref_doc.referral_amount = amount
                ref_doc.save(ignore_permissions=True)
                trigger_event(doc=ref_doc, event_name="referral_created")

                if frappe.db.exists("Fees", {"student": referred_by}):
                    fees = frappe.get_doc("Fees", {"student": referred_by})
                    discount_amount = float(ref_doc.referral_amount) - previous_referral_amount
                    update_referral_discount(fees, discount_amount)
        else:
            amount = referral_amounts.get(1)
            amount = float(amount) if amount else 0
            ref_doc = frappe.new_doc("Referral Log")
            ref_doc.student_id = referred_by
            ref_doc.number_of_referral = 1
            ref_doc.referral_amount = amount
            ref_doc.student_email_id = student_email_id
            ref_doc.save(ignore_permissions=True)
            
            trigger_event(doc=ref_doc, event_name="referral_created")
            if frappe.db.exists("Fees", {"student": referred_by}):
                fees = frappe.get_doc("Fees", {"student": referred_by})
                apply_referrral_discount(fees, amount)
    except Exception as e:
        frappe.logger('edu_quality').exception(e)



def apply_referrral_discount(doc, referral_amount):
    filters = {"type": "Referral", "enabled": 1}
    if frappe.db.exists("Referral Log", {"student_id": doc.student}):
        ref = frappe.get_doc("Referral Log", {"student_id": doc.student})
        discount = float(ref.referral_amount)
        for component in doc.components:
            amount = component.custom_amount_after_discount
            amount = amount if amount else component.amount
            if amount > discount and discount != 0:
                if frappe.db.exists("Discount Configuration", filters):
                    dis = frappe.get_doc("Discount Configuration", filters)
                    discount_list = get_discount_list(component.custom_discounts)
                    # if other discount is already present
                    if discount_list and dis.name not in discount_list:
                        discount_list.append(dis.name)
                        discount_name = ", ".join(discount_list)
                        discounted_amount = (
                            referral_amount + component.custom_discount_amount
                        )
                        amount = component.amount - discounted_amount
                        discount = calculate_discount(
                            component.amount, discounted_amount
                        )
                        update_component(
                            component.name,
                            discount_name,
                            discount,
                            discounted_amount,
                            referral_amount,
                            amount,
                            doc,
                        )
                        update_payment_plan_after_discount(doc, referral_amount, apply_discount=True)

                        break
                    else:
                        discount_name = dis.name
                        amount = component.custom_amount_after_discount
                        amount = amount if amount else component.amount
                        total_discount = component.custom_discount_amount + discount
                        discounted_amount = amount - total_discount
                        discount_percentage = calculate_discount(amount, total_discount)
                        update_component(
                            component.name,
                            discount_name,
                            discount_percentage,
                            total_discount,
                            total_discount,
                            discounted_amount,
                            doc,
                        )
                        update_payment_plan_after_discount(doc, total_discount, apply_discount=True)
                        break


def update_referral_discount(doc, discount_amount):
    for component in doc.components:
        discount_name = component.custom_discounts
        if discount_name and "referral" in discount_name.lower():
            amount = component.custom_amount_after_discount - discount_amount
            grand_total = doc.grand_total - discount_amount
            outstanding_amount = doc.outstanding_amount - discount_amount
            previous_discount = component.custom_discount_amount
            new_discount = previous_discount + discount_amount
            discount_percentage = calculate_discount(component.amount, new_discount)
            frappe.db.set_value("Fee Component", component.name, "custom_discount_amount", new_discount)
            frappe.db.set_value("Fee Component", component.name, "custom_amount_after_discount", amount)
            frappe.db.set_value("Fee Component", component.name, "custom_discount_percentage", discount_percentage)
            grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
            frappe.db.set_value("Fees", doc.name, "grand_total", grand_total)
            frappe.db.set_value("Fees", doc.name, "grand_total_in_words", grand_total_in_words)
            frappe.db.set_value("Fees", doc.name, "outstanding_amount", outstanding_amount)
            update_payment_plan_after_discount(doc, discount_amount, apply_discount=True)
            break;
        else:
            apply_referrral_discount(doc, discount_amount)