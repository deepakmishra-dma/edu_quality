import frappe 

from edu_quality.public.py.discount import (
    calculate_discount,
    get_discount_list,
    update_component,
    update_total_discount_in_fees,
    update_payment_plan_after_discount,
    get_label
)


def after_insert(doc, method=None):
    pass



def add_referral_discount(referred_by):
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

        try:
            from nextai.funnel.custom_trigger import trigger_event
            trigger_event(doc=student, event_name="referral_created")
        except ImportError:
            print("Chatnext is not installed")
    
        outstanding_fees = get_outstanding_fees(student)
        if outstanding_fees:
            update_referral_discount(outstanding_fees, discount_amount)
        else:
            student.referral_amount = student.referral_amount + discount_amount 
            student.save()

    except Exception as e:
        frappe.logger('referral').exception(e)


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
        ["Fees","outstanding_amount", ">", 0],
        ["Fees",'docstatus', "=", 1]
    ]
    if frappe.db.exists("Fees",filters):
        return frappe.get_doc("Fees",filters)
    return None


def update_referral_discount(doc, discount_amount):
    """
    Update the referral discount for a document.

    Parameters:
    - doc (frappe.Fees): The document to update with the referral discount.
    - discount_amount (float): The amount of referral discount to apply.
    """
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

            grand_total = doc.grand_total - discount_amount
            grand_total_in_words = frappe.utils.in_words(grand_total).title()

            doc_updates = {
                "grand_total": grand_total,
                "grand_total_in_words": grand_total_in_words,
                "outstanding_amount": doc.outstanding_amount - discount_amount
            }

            frappe.db.set_value("Fees", doc.name, doc_updates)
            doc.add_discount_entry(component.custom_company, discount_amount)
            update_total_discount_in_fees(doc.name)
            update_payment_plan_after_discount(doc, discount_amount, apply_discount=True,dis={"type":"Referral"})

            return 
        
    apply_referral_discount(doc, discount_amount)


def apply_referral_discount(doc, referral_amount):
    """
    Apply referral discount to a document's components with 'Tution Fee' category.

    Parameters:
    - doc (frappe.Fees): The document to apply the referral discount to.
    - referral_amount (float): The amount of referral discount to apply.

    Note:
    This function updates the document's components by applying the referral discount
    based on the 'Tution Fee' category. If the discount is not already present,
    it adds 'Referral' to the existing discounts.
    """
    for component in doc.components:
        if component.fees_category != "Tution Fee":
            continue

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
            doc.add_discount_entry(component.custom_company, referral_amount)
            update_total_discount_in_fees(doc.name)
            update_payment_plan_after_discount(doc, total_discount, apply_discount=True,dis={"type":"Referral"})
            return 



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
        if not component.fees_category != "Tution Fee":
            continue

        if component.amount > discount and discount != 0:

            amount = component.custom_amount_after_discount or component.amount
            amount_after_discount = amount - discount
            new_discount = component.custom_discount_amount + discount
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
                "outstanding_amount": doc.outstanding_amount - discount
            }

            frappe.db.set_value("Fees", doc.name, doc_updates)

            label = get_label(component.fees_category)
            ref_dis[label] = {component.fees_category:discount}
            doc.add_discount_entry(component.custom_company, discount)
            return ref_dis
                
            
   
    