import frappe 

from edu_quality.public.py.discount import (
    calculate_discount,
    get_discount_list,
    update_component,
    update_total_discount_in_fees,
    update_payment_plan_after_discount,
    get_label,
    update_breakups
)

from edu_quality.public.py.payment_request import update_payment_request_after_discount
from frappe.auth import LoginManager



@frappe.whitelist(allow_guest=True)
def get_web_form(hash):
    if frappe.db.exists("Student Applicant",{'form_hash':hash}):
        student_applicant = frappe.db.get_value("Student Applicant",{'form_hash':hash},'name')
        if frappe.db.exists("User Permission",{'allow':"Student Applicant",'for_value':student_applicant}):
            user = frappe.db.get_value("User Permission",{'allow':"Student Applicant",'for_value':student_applicant},'user')
            login_manager = LoginManager()
            login_manager.login_as(user)
            return frappe.utils.get_url() + "/walnut-school-student-application/" + student_applicant + "/edit"
        frappe.throw("User Not set for this Application!")
    frappe.throw("Application Not Found!")

def set_guardian_permissions(doc):
    for guardian in doc.guardians:
        user = frappe.db.get_value("Guardian",guardian.guardian,"user")
        if not user:
            continue
        if not frappe.db.exists("User Permission",{"user":user,"allow":"Student Applicant","for_value":doc.name}):
            perm = frappe.new_doc("User Permission")
            perm.user = user
            perm.allow = "Student Applicant"
            perm.for_value = doc.name
            perm.insert(ignore_permissions=True)

def after_insert(doc,method=None):
    doc.form_hash = generate_hash(doc.name)
    doc.save(ignore_permissions=True)
    set_guardian_permissions(doc)
    try:
        from nextai.funnel.custom_trigger import trigger_event
        trigger_event(doc=doc, event_name="student_applicant_created")
    except ImportError as e:
        frappe.logger('student_applicant_creation').exception(e)


def update_guardian_details(doc):
    try:
        mother_updated = 0 
        guardian_updated = 0
        for guardian in doc.guardians:
            guardian_doc = frappe.get_doc("Guardian", guardian.guardian)
            if guardian.relation == 'Father':
                frappe.logger('update').exception('father')
                guardian_doc.first_name = doc.fathers_first_name
                guardian_doc.last_name = doc.fathers_last_name
                guardian_doc.email_address = doc.fathers_email_id
                guardian_doc.middle_name = doc.fathers_middle_name
                name = doc.fathers_first_name + " " + doc.fathers_last_name
                if name:
                    guardian_doc.guardian_name = name
                guardian_doc.mobile_number = doc.fathers_mobile_number
                guardian_doc.education = doc.fathers_education_qualification
                guardian_doc.occupation = doc.fathers_profession 
                guardian_doc.annual_income = doc.fathers_annual_income
                guardian_doc.company_name = doc.fathers_office_name
                guardian_doc.designation = doc.fathers_designation
                guardian_doc.work_address = doc.fathers_office_address
                guardian_doc.parent_status = doc.select_parent
                guardian_doc.if_divorced = doc.parent_divorced
                guardian_doc.address_line_1  = doc.address_line_1
                guardian_doc.address_line_2  = doc.address_line_2
                guardian_doc.city  = doc.city
                guardian_doc.pincode  = doc.pincode
                guardian_doc.save(ignore_permissions=True)
            elif guardian.relation == 'Mother':
                mother_updated = 1
                guardian_doc.first_name = doc.mother_first_name
                guardian_doc.last_name = doc.mother_last_name
                guardian_doc.email_address = doc.mother_email_id
                guardian_doc.middle_name = doc.mother_middle_name
                name = doc.mother_first_name + " " + doc.mother_last_name
                if name:
                    guardian_doc.guardian_name = name
                guardian_doc.mobile_number = doc.mother_mobile_number
                guardian_doc.education = doc.mother_education_qualification
                guardian_doc.occupation = doc.mother_profession
                guardian_doc.annual_income = doc.mother_annual_income
                guardian_doc.company_name = doc.mother_office_name
                guardian_doc.designation = doc.mother_designation
                guardian_doc.work_address = doc.mother_office_address
                guardian_doc.parent_status = doc.select_parent
                guardian_doc.if_divorced = doc.parent_divorced
                guardian_doc.address_line_1  = doc.address_line_1
                guardian_doc.address_line_2  = doc.address_line_2
                guardian_doc.city  = doc.city
                guardian_doc.pincode  = doc.pincode
                guardian_doc.save(ignore_permissions=True)
            elif guardian.relation == 'Guardian':
                guardian_updated = 1
                guardian_doc.first_name = doc.guardian_first_name
                guardian_doc.last_name = doc.guardian_last_name
                guardian_doc.email_address = doc.guardian_email_id
                guardian_doc.middle_name = doc.guardian_middle_name
                name = doc.guardian_first_name + " " + doc.guardian_last_name if doc.guardian_last_name else ""
                if name:
                    guardian_doc.guardian_name = name
                guardian_doc.mobile_number = doc.guardian_mobile_number
                guardian_doc.education = doc.guardian_education_qualification
                guardian_doc.occupation = doc.guardian_profession
                guardian_doc.annual_income = doc.guardian_annual_income
                guardian_doc.company_name = doc.guardian_office_name
                guardian_doc.designation = doc.guardian_designation
                guardian_doc.work_address = doc.guardian_office_address
                guardian_doc.parent_status = doc.select_parent
                guardian_doc.if_divorced = doc.parent_divorced
                guardian_doc.address_line_1  = doc.address_line_1
                guardian_doc.address_line_2  = doc.address_line_2
                guardian_doc.city  = doc.city
                guardian_doc.pincode  = doc.pincode
                guardian_doc.save(ignore_permissions=True)
        if doc.mother_first_name and mother_updated == 0:
            guardian_doc = frappe.new_doc("Guardian")
            guardian_doc.first_name = doc.mother_first_name
            guardian_doc.last_name = doc.mother_last_name
            guardian_doc.email_address = doc.mother_email_id
            guardian_doc.middle_name = doc.mother_middle_name
            name = doc.mother_first_name + " " + doc.mother_last_name
            if name:
                guardian_doc.guardian_name = name
            guardian_doc.mobile_number = doc.mother_mobile_number
            guardian_doc.education = doc.mother_education_qualification
            guardian_doc.occupation = doc.mother_profession
            guardian_doc.annual_income = doc.mother_annual_income
            guardian_doc.company_name = doc.mother_office_name
            guardian_doc.designation = doc.mother_designation
            guardian_doc.work_address = doc.mother_office_address
            guardian_doc.parent_status = doc.select_parent
            guardian_doc.if_divorced = doc.parent_divorced
            guardian_doc.address_line_1  = doc.address_line_1
            guardian_doc.address_line_2  = doc.address_line_2
            guardian_doc.city  = doc.city
            guardian_doc.pincode  = doc.pincode
            guardian_doc.save(ignore_permissions=True)
            doc.append('guardians', {
                'guardian': guardian_doc.name,
                'guardian_name': guardian_doc.guardian_name,
                'relation': 'Mother'
            })
        if doc.guardian_first_name and guardian_updated == 0:
            guardian_doc = frappe.new_doc("Guardian")
            guardian_doc.first_name = doc.guardian_first_name
            guardian_doc.last_name = doc.guardian_last_name
            guardian_doc.email_address = doc.guardian_email_id
            guardian_doc.middle_name = doc.guardian_middle_name
            name = doc.guardian_first_name + " " + doc.guardian_last_name if doc.guardian_last_name else ""
            if name:
                guardian_doc.guardian_name = name
            guardian_doc.mobile_number = doc.guardian_mobile_number
            guardian_doc.education = doc.guardian_education_qualification
            guardian_doc.occupation = doc.guardian_profession
            guardian_doc.annual_income = doc.guardian_annual_income
            guardian_doc.company_name = doc.guardian_office_name
            guardian_doc.designation = doc.guardian_designation
            guardian_doc.work_address = doc.guardian_office_address
            guardian_doc.parent_status = doc.select_parent
            guardian_doc.if_divorced = doc.parent_divorced
            guardian_doc.address_line_1  = doc.address_line_1
            guardian_doc.address_line_2  = doc.address_line_2
            guardian_doc.city  = doc.city
            guardian_doc.pincode  = doc.pincode
            guardian_doc.save(ignore_permissions=True)
            doc.append('guardians', {
                'guardian': guardian_doc.name,
                'guardian_name': guardian_doc.guardian_name,
                'relation': 'Guardian'
            })
    except Exception as e:
        frappe.logger('update').exception(e)            
            




def on_update(doc,method=None):
    set_guardian_permissions(doc)
    update_guardian_details(doc)


def generate_hash(val):
    return frappe.generate_hash(val, length=20)



def add_referral_discount(referred_by, student_applicant=None):
    """
    Add referral discount for a student based on the number of referrals.

    Parameters:
    - referred_by (str): The student ID who referred others.
    """
    try:
        student = frappe.get_doc('Student', referred_by)
        if student.is_rte:
            return
        increase_referral_count(student)

        discount_amount = get_referral_amount(student.number_of_referrals)
    
        outstanding_fees = get_outstanding_fees(student)
        if outstanding_fees:
            update_referral_discount(outstanding_fees, discount_amount)
        else:
            student.referral_amount = student.referral_amount + discount_amount 
            student.save()
        
        try:
            if student_applicant:
                from nextai.funnel.custom_trigger import trigger_event
                trigger_event(doc=student_applicant, event_name="referral_created")
        except ImportError:
            print("Chatnext is not installed")
            return 0
        return 1

    except Exception as e:
        frappe.logger('referral').exception(e)
        return 0


def increase_referral_count(student):
    """
    Increase the referral count for a student and save the document.

    Parameters:
    - student (frappe.Student): The Student document to update.
    """
    student.number_of_referrals += 1
    student.save()



def get_referral_amount(ref_no):
    """
    Retrieve the referral amount based on the given reference number.

    Parameters:
    - ref_no (int): The reference number used to look up the corresponding referral amount.
    """
    referral_settings = frappe.get_single("Referral Settings")
    referral_amounts = {r.get('idx'): r.get('referral_amount') for r in referral_settings.referral}
    max_idx = max(referral_amounts)
    return float(referral_amounts.get(int(ref_no), referral_amounts[max_idx]))


def get_outstanding_fees(student):
    """
    Retrieve outstanding fees document for a student.

    Parameters:
    - student (frappe.Student): The Student document.

    Returns:
    - frappe.Fees: The Fees document with outstanding amount for the student.
    """
    filters = [
        ["Fees","student", "=", student.name],
        ["Fees","outstanding_amount", "!=", 0],
        ["Fees",'docstatus', "=", 1]
    ]
    if frappe.db.exists("Fees",filters):
        return frappe.get_doc("Fees",filters)
    return None


def update_referral_discount(doc, discount_amount,is_paid=False):
    """
    Update the referral discount for a document.

    Parameters:
    - doc (frappe.Fees): The document to update with the referral discount.
    - discount_amount (float): The amount of referral discount to apply.
    """
    try:
        for component in doc.components:
            discount_name = component.custom_discounts
            if discount_name and "referral" in discount_name.lower():
                amount_after_discount = component.custom_amount_after_discount - discount_amount
                new_discount = component.custom_discount_amount + discount_amount
                discount_percentage = calculate_discount(component.amount, new_discount)

                updates = {
                    "custom_discount_amount": new_discount,
                    "custom_amount_after_discount": amount_after_discount,
                    "custom_discount_percentage": discount_percentage
                }

                frappe.db.set_value("Fee Component", component.name, updates)

                dis = {
                "name": "Referral",
                "discount": None,
                "discount_amount": discount_amount,
                }

                update_breakups(dis, component, doc,term=1,update=1)

                grand_total = doc.grand_total - discount_amount
                grand_total_in_words = frappe.utils.in_words(grand_total).title()

                doc_updates = {
                    "grand_total": grand_total,
                    "grand_total_in_words": grand_total_in_words,
                    "outstanding_amount": doc.outstanding_amount - discount_amount,
                    "total_discount": doc.total_discount + discount_amount
                }
                if not is_paid:
                    frappe.db.set_value("Fees", doc.name, doc_updates)
                doc.reload()
                doc.add_discount_entry(component.custom_company, discount_amount)
                update_total_discount_in_fees(doc.name)
                update_payment_plan_after_discount(doc, discount_amount, apply_discount=True,dis={"type":"Referral"})
                if not is_paid:
                    update_payment_request_after_discount(doc)
                doc.update_split()
                return 
            
        apply_referral_discount(doc, discount_amount,is_paid)
    except Exception as e:
        frappe.logger('referral').exception(e)


def apply_referral_discount(doc, referral_amount,is_paid=False):
    """
    Apply referral discount to a document's components with 'Tuition Fee' category.

    Parameters:
    - doc (frappe.Fees): The document to apply the referral discount to.
    - referral_amount (float): The amount of referral discount to apply.

    Note:
    This function updates the document's components by applying the referral discount
    based on the 'Tuition Fee' category. If the discount is not already present,
    it adds 'Referral' to the existing discounts.
    """
    try:
        for component in doc.components:
            if not component.fees_category in ["Tuition Fee", 'Tuition Fee (KG)']:
                continue
            dis = {
                "name": "Referral",
                "discount": None,
                "discount_amount": referral_amount,
            }

            update_breakups(dis, component, doc,term=1,update=1)

            amount = component.custom_amount_after_discount or component.amount

            if amount > referral_amount and referral_amount != 0:
                discount_list = get_discount_list(component.custom_discounts)

                # Check if "Referral" is already present in discount_list
                if not discount_list or "Referral" not in discount_list:
                    discount_list.append("Referral")
                    discount_name = ", ".join(discount_list)
                else:
                    discount_name = "Referral"

                total_discount = component.custom_discount_amount + referral_amount
                discounted_amount = component.amount - total_discount
                discount_percentage = calculate_discount(amount, total_discount)

                update_component(
                    component.name,
                    discount_name,
                    discount_percentage,
                    total_discount,
                    referral_amount,
                    discounted_amount,
                    doc,
                )
                doc.reload()
                doc.add_discount_entry(component.custom_company, referral_amount)
                update_total_discount_in_fees(doc.name)
                update_payment_plan_after_discount(doc, referral_amount, apply_discount=True,dis={"type":"Referral"})
                if not is_paid:
                    update_payment_request_after_discount(doc)
                doc.update_split()
                return 
    except Exception as e:
        frappe.logger('referral').exception(e)


def referal_discount(doc, method=None):
    """
    Apply referral discount to eligible fee components and update the document when creating fee document.

    Parameters:
    - doc (frappe.model.document.Document): The document to which the referral discount is applied.
    - method (str, optional): The method triggering the referral discount application.

    Returns:
    dict: A dictionary containing information about the applied referral discount per fee category.
    """
    grand_total = doc.grand_total
    ref_dis = {}
    student = frappe.get_doc("Student",doc.student)

    if student.is_rte or student.referral_amount == 0:
        return
        
    discount = float(student.referral_amount)

    for component in doc.components:
        if not component.fees_category != "Tuition Fee":
            continue

        if component.amount > discount and discount != 0:
            dis = {
                "name": "Referral",
                "discount": None,
                "discount_amount": discount,
            }
            update_breakups(dis, component, doc, term=1)

            amount = component.custom_amount_after_discount or component.amount
            amount_after_discount = amount - discount
            new_discount = component.custom_discount_amount or 0 + discount
            discount_percentage = calculate_discount(component.amount, new_discount)

            discount_name = component.custom_discounts
            discount_list = get_discount_list(discount_name)

            if discount_list and "Referral" not in discount_list:
                discount_list.append("Referral")
                discount_name = ", ".join(discount_list)
            else:
                discount_name = "Referral"

            updates = {
                "custom_discounts": discount_name,
                "custom_discount_amount": new_discount,
                "custom_amount_after_discount": amount_after_discount,
                "custom_discount_percentage": discount_percentage
            }

            frappe.db.set_value("Fee Component", component.name, updates)


            grand_total = doc.grand_total - discount
            doc.grand_total = grand_total
            grand_total_in_words = str(frappe.utils.in_words(doc.grand_total)).title()

            doc_updates = {
                "grand_total": grand_total,
                "grand_total_in_words": grand_total_in_words,
                "outstanding_amount": doc.outstanding_amount - discount,
                "total_discount": (doc.total_discount or 0) + discount
            }

            frappe.db.set_value("Fees", doc.name, doc_updates)

            label = get_label(component.fees_category)
            ref_dis[label] = {component.fees_category:discount}
            doc.add_discount_entry(component.custom_company, discount)
            return ref_dis
                
            
   
    