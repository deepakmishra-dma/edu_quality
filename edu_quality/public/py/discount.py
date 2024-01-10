from datetime import datetime
from edu_quality.overrides import make_payment_request
from edu_quality.public.py.payment_request import update_payment_request_after_discount
import frappe
from frappe.utils import today, getdate, flt


@frappe.whitelist()
def add_discount(fee_name, discount,fees=None):
    discount_applied = False
    grand_discount_amount = 0
    if not fees:
        fees = frappe.get_doc("Fees", fee_name)
    dis = frappe.get_doc("Discount Configuration", discount)
    company = None
    for component in fees.components:
        if component.fees_category == dis.fee_category:
            company = component.custom_company
            discount_name = component.custom_discounts
            if discount_name and dis.can_be_applied_with_other_discounts == 1:
                discount_list = get_discount_list(discount_name)
                # if the discount is already present and the new discount could be applied with other discounts
                if dis.name not in discount_list:
                    discount_list.append(dis.name)
                    discount_name = ", ".join(discount_list)
                    if dis.discount_amount:
                        grand_discount_amount = dis.discount_amount
                        discounted_amount = grand_discount_amount + component.custom_discount_amount
                        amount = component.amount - discounted_amount
                        discount = calculate_discount(component.amount, discounted_amount)
                        update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees)
                        message = dis.name + " Discount applied successfully"
                        discount_applied = True
                        frappe.response['message'] = message
                    else:
                        amount = component.amount
                        grand_discount_amount = (amount * float(dis.discount)) / 100
                        discounted_amount = grand_discount_amount + component.custom_discount_amount
                        discount = calculate_discount(component.amount, discounted_amount)
                        amount = amount - discounted_amount
                        update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees)
                        message = dis.name + " Discount applied successfully"
                        discount_applied = True
                        frappe.response['message'] = message
                else:
                    frappe.response['message'] = "Discount already applied"
            elif discount_name and dis.can_be_applied_with_other_discounts == 0:
                discount_list = get_discount_list(discount_name)
                if dis.name in discount_list:
                    message = dis.name + " Discount already present"
                    frappe.response['message'] = message
                else:
                    message = dis.name + " Discount can not be applied with other discounts"
                    frappe.response['message'] = message
                # if the discount is already present and the new discount could not be applied with other discounts
            else:
                # if the discount is not already present
                discount_name = dis.name
                if dis.discount_amount:
                    discounted_amount = grand_discount_amount = dis.discount_amount
                    amount = component.amount - discounted_amount
                    discount = calculate_discount(component.amount, discounted_amount)
                    update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees)
                    message = dis.name + " Discount applied successfully"
                    discount_applied = True
                    frappe.response['message'] = message
                else:
                    grand_discount_amount = (component.amount * float(dis.discount)) / 100
                    discounted_amount = grand_discount_amount
                    amount = component.amount - discounted_amount
                    update_component(component.name, discount_name, dis.discount, discounted_amount, grand_discount_amount, amount, fees)
                    message = dis.name + " Discount applied successfully"
                    discount_applied = True
                    frappe.response['message'] = message
    if discount_applied:
        fees.add_discount_entry(company, grand_discount_amount)
        update_total_discount_in_fees(fees.name)
        if dis.needs_admin_approval:
            frappe.db.set_value("Fees",fee_name,"workflow_state","Pending")
            update_payment_plan_after_discount(fees, grand_discount_amount, apply_discount=True,dis=dis)
        else:
            update_payment_plan_after_discount(fees, grand_discount_amount, apply_discount=True,dis=dis)
            update_payment_request_after_discount(fees)


@frappe.whitelist()
def remove_discount(fee_name, discount, update_payment_request=True):
    discount_removed = False
    grand_discount_amount = 0
    fees = frappe.get_doc("Fees", fee_name)
    dis = frappe.get_doc("Discount Configuration", discount)
    company = None

    for component in fees.components:
        if component.custom_discounts:
            company = component.custom_company
            discount_list = get_discount_list(component.custom_discounts)
            if component.fees_category == dis.fee_category and discount in discount_list:
                if dis.discount_amount:
                    grand_discount_amount = dis.discount_amount
                    amount = component.custom_amount_after_discount + grand_discount_amount
                    discount_amount = component.custom_discount_amount - grand_discount_amount
                    discount = calculate_discount(component.amount, discount_amount)
                    discount_list.remove(dis.name)
                    discount_name = ", ".join(discount_list)
                    # updating the data in the database
                    remove_and_update_component(component.name, discount_name, discount, discount_amount, grand_discount_amount, amount, fees)
                    message = dis.name + " Discount removed successfully"
                    discount_removed = True
                    frappe.response['message'] = message
                else:
                    grand_discount_amount = (component.amount * float(dis.discount)) / 100
                    amount = component.custom_amount_after_discount + grand_discount_amount
                    discount_amount = component.custom_discount_amount - grand_discount_amount
                    discount = calculate_discount(component.amount, discount_amount)
                    discount_list.remove(dis.name)
                    discount_name = ", ".join(discount_list)
                    # updating the data in the database
                    remove_and_update_component(component.name, discount_name, discount, discount_amount, grand_discount_amount, amount, fees)
                    message = dis.name + " Discount removed successfully"
                    discount_removed = True
                    frappe.response['message'] = message
            elif discount not in discount_list:
                message = dis.name + " Discount does not present"
                frappe.response['message'] = message
    if discount_removed:
        fees.remove_discount_entry(company, grand_discount_amount)
        update_total_discount_in_fees(fees.name)
        update_payment_plan_after_discount(fees, grand_discount_amount, apply_discount=False,dis=dis)
        if update_payment_request:
            update_payment_request_after_discount(fees)


def update_total_discount_in_fees(fee_name):
    fees = frappe.get_doc("Fees", fee_name)
    fees.total_discount = get_all_discounts(fees)
    fees.save(ignore_permissions=True)


def get_all_discounts(doc,method=None):
    discounts = 0
    for component in doc.components:
        if component.custom_discount_amount:
            discounts += component.custom_discount_amount
    return discounts

def get_discount_list(input_string):
    if input_string is None:
        return []
    split_strings = input_string.split(',')
    stripped_values = [value.strip() for value in split_strings]
    return stripped_values


def calculate_discount(amount, discounted_amount):
    discount = 100 - ((amount - discounted_amount) / amount) * 100
    return discount

# updating the data in the database
def update_component(component_name, discount_name, final_discount, discounted_amount, grand_discount_amount, amount, fees):
    frappe.db.set_value("Fee Component", component_name, "custom_discounts", discount_name)
    frappe.db.set_value("Fee Component", component_name, "custom_discount_percentage", final_discount)
    frappe.db.set_value("Fee Component", component_name, "custom_discount_amount", discounted_amount)
    frappe.db.set_value("Fee Component", component_name, "custom_amount_after_discount", amount)
    grand_total = fees.grand_total - grand_discount_amount
    outstanding_amount = fees.outstanding_amount - grand_discount_amount
    grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
    frappe.db.set_value("Fees", fees.name, "grand_total", grand_total)
    frappe.db.set_value("Fees", fees.name, "grand_total_in_words", grand_total_in_words)
    frappe.db.set_value("Fees", fees.name, "outstanding_amount", outstanding_amount)


def remove_and_update_component(component_name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees):
    frappe.db.set_value("Fee Component", component_name, "custom_discounts", discount_name)
    frappe.db.set_value("Fee Component", component_name, "custom_discount_percentage", discount)
    frappe.db.set_value("Fee Component", component_name, "custom_amount_after_discount", amount)
    if discounted_amount:
        frappe.db.set_value("Fee Component", component_name, "custom_discount_amount", discounted_amount)
        grand_total = fees.grand_total + grand_discount_amount
        outstanding_amount = fees.outstanding_amount + grand_discount_amount
    else:
        frappe.db.set_value("Fee Component", component_name, "custom_discount_amount", 0)
        grand_total = fees.grand_total + grand_discount_amount
        outstanding_amount = fees.outstanding_amount + grand_discount_amount

    grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
    frappe.db.set_value("Fees", fees.name, "grand_total", grand_total)
    frappe.db.set_value("Fees", fees.name, "grand_total_in_words", grand_total_in_words)
    frappe.db.set_value("Fees", fees.name, "outstanding_amount", outstanding_amount)


def get_label(fee_category):
    label = frappe.get_value("Fee Category", fee_category, "custom_label")
    if label:
        label = label.split("-")[0].strip()
    else:
        label = frappe.get_value("Fees Settings", None, "default_account").split("-")[0].strip()
    return label


def payment_plan(doc, method=None):
    pe = frappe.get_doc("Program Enrollment", doc.program_enrollment)
    if pe.custom_payment_plan is not None:
        doc.payment_plan = pe.custom_payment_plan
    else:
        doc.payment_plan = frappe.db.get_value("Fee Schedule",doc.fee_schedule,'payment_plan')
    if doc.payment_plan:
        pp = frappe.get_doc("Payment Plan",doc.payment_plan)
        doc.payment_schedule = []
        initial_payment = 0
        regular_amount = 0
        for component in doc.components:
            if component.fee_type and component.fee_type!= "Regular":
                initial_payment = initial_payment +  component.amount
            else:
                regular_amount += component.amount
        i=0
        for schedule in pp.payment_schedule:
            payment_amount = flt(regular_amount * schedule.invoice_portion/100,2)
            description = "Installment - " + str(i+1)
            if i==0 and initial_payment>0:
                before_days = frappe.db.get_value("Fee Schedule",doc.fee_schedule,"create_payment_request_before")
                today = datetime.today().date()
                difference = schedule.due_date - today
                if difference.days > before_days:
                        only_deposit(doc)
                else:
                    payment_amount = payment_amount + initial_payment
                    description = description + " and deposit/application fee"
                    frappe.enqueue(
                            "edu_quality.public.py.student.create_payment_request",
                            fee=doc,
                            term = schedule.payment_term,
                            is_async=True,
                            queue="long",
                            timeout=1800,
                        )
            i = i+1
            doc.append("payment_schedule",{
                'payment_term': schedule.payment_term,
                'description': description,
                'due_date': schedule.due_date,
                'invoice_portion': schedule.invoice_portion,
                'payment_amount': payment_amount,
                'outstanding': payment_amount,
            })


def only_deposit(doc):    
    make_payment_request(
        party_type="Student",
        party=doc.student,
        dt="Fees",
        dn=doc.name,
        is_deposit=True,
        recipient_id=doc.student_email,
        submit_doc=True
    )


def time_based_discount(doc):
    for component in doc.components:
        if frappe.db.exists(
            "Discount Configuration",
            {
                "fee_structure": doc.fee_structure,
                "fee_category": component.fees_category,
                "type": "Time Based",
                "enabled": 1,
            },
        ):            
            dis = frappe.get_doc(
                "Discount Configuration",
                {
                    "fee_structure": doc.fee_structure,
                    "fee_category": component.fees_category,
                    "type": "Time Based",
                    "enabled": 1,
                },
            )
            if dis.start_date <= getdate(today()) <= dis.end_date:
                discount_amount = apply_time_based_discount(dis, component, doc)
                doc.add_discount_entry(component.custom_company, discount_amount)
                label = get_label(component.fees_category)
                return {label:{component.fees_category:discount_amount}
}


def apply_time_based_discount(dis, component, fees):
    # if the discount is not already present
    if dis.discount_amount:
        discounted_amount = dis.discount_amount
        amount = component.amount - discounted_amount
        discount = calculate_discount(component.amount, discounted_amount)
        component.custom_discounts = dis.name
        component.custom_discount_percentage = discount
        component.custom_discount_amount = discounted_amount
        component.custom_amount_after_discount = amount
        grand_total = fees.grand_total - discounted_amount
        grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
        fees.grand_total = grand_total
        fees.grand_total_in_words = grand_total_in_words
        fees.outstanding_amount = grand_total
        return dis.discount_amount
    else:
        discount_amount = (component.amount * float(dis.discount)) / 100
        amount = component.amount - discount_amount
        component.custom_discounts = dis.name
        component.custom_discount_percentage = dis.discount
        component.custom_discount_amount = discount_amount
        component.custom_amount_after_discount = amount
        grand_total = fees.grand_total - discount_amount
        grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
        fees.grand_total = grand_total
        fees.grand_total_in_words = grand_total_in_words
        fees.outstanding_amount = grand_total
        return discount_amount

def update_payment_plan_after_discount(doc, total_discount=0, apply_discount=False,dis={}):
    if doc.payment_plan:
        for i, schedule in enumerate(doc.payment_schedule):
            if schedule.outstanding == 0:
                continue
            if apply_discount:
                if dis.get('type') != "Payment Plan":
                    amount = schedule.outstanding - total_discount
                    frappe.db.set_value("Payment Schedule",schedule.name,"payment_amount",amount)
                    frappe.db.set_value("Payment Schedule",schedule.name,"outstanding",amount)
                    break
                else:
                    if i == len(doc.payment_schedule) - 1:
                        amount = schedule.outstanding - total_discount
                        frappe.db.set_value("Payment Schedule",schedule.name,"payment_amount",amount)
                        frappe.db.set_value("Payment Schedule",schedule.name,"outstanding",amount)


            else:
                if dis.get('type') != "Payment Plan":
                    amount = schedule.outstanding + total_discount
                    frappe.db.set_value("Payment Schedule",schedule.name,"payment_amount",amount)
                    frappe.db.set_value("Payment Schedule",schedule.name,"outstanding",amount)
                    break
                else:
                    if i == len(doc.payment_schedule) - 1:
                        amount = schedule.outstanding - total_discount
                        frappe.db.set_value("Payment Schedule",schedule.name,"payment_amount",amount)
                        frappe.db.set_value("Payment Schedule",schedule.name,"outstanding",amount)


def get_payment_plan_discount(payment_plan, doc):
    for component in doc.components:
        dis_filter = {"payment_plan": payment_plan, "fee_structure":doc.fee_structure, "fee_category": component.fees_category, "enabled":1}
        if frappe.db.exists("Discount Configuration", dis_filter):
            dis = frappe.get_doc("Discount Configuration", dis_filter)
            if dis.discount_amount:
                component.custom_discounts = dis.name
                component.custom_discount_percentage = calculate_discount(component.amount, dis.discount_amount)
                component.custom_discount_amount = dis.discount_amount
                component.custom_amount_after_discount = component.amount - dis.discount_amount
                grand_total = doc.grand_total - dis.discount_amount
                grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
                doc.grand_total = grand_total
                doc.grand_total_in_words = grand_total_in_words
                doc.outstanding_amount = grand_total
                doc.add_discount_entry(component.custom_company, dis.discount_amount)
                return (dis.discount_amount, "Amount", 0)
            else:
                discount_amount = (component.amount * float(dis.discount)) / 100
                component.custom_discounts = dis.name
                component.custom_discount_percentage = dis.discount
                component.custom_discount_amount = discount_amount
                component.custom_amount_after_discount = component.amount - discount_amount
                grand_total = doc.grand_total - discount_amount
                grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
                doc.grand_total = grand_total
                doc.grand_total_in_words = grand_total_in_words
                doc.outstanding_amount = grand_total
                doc.add_discount_entry(component.custom_company, discount_amount)
                return (discount_amount, "Percentage", dis.discount)
    return None



            

def update_payment_schedule(doc, payment_plan=None):
    try:
        if not payment_plan:
            payment_plan = doc.payment_plan
        payment_plan_discount = get_payment_plan_discount(payment_plan, doc)
        other_discount = 0
        for component in doc.components:
            if component.custom_discounts:
                discount_name = component.custom_discounts.lower()
                discount_amount = component.custom_discount_amount
                if discount_amount and "payment plan" not in discount_name:
                    other_discount += component.custom_discount_amount
        
        discount_applied = False
        discount_amount = 0
        for i, schedule in enumerate(doc.payment_schedule):
            if not discount_applied:
                amount = schedule.outstanding - other_discount
                schedule.payment_amount = amount
                schedule.outstanding = amount
                schedule.discount = other_discount
                schedule.discount_type = "Amount"
                schedule.discount_date = schedule.due_date
                discount_applied = True

            elif i == len(doc.payment_schedule) - 1:
                if payment_plan_discount and payment_plan_discount[1] == "Amount":
                    discount_amount = payment_plan_discount[0]
                    amount = schedule.outstanding - payment_plan_discount[0]
                    schedule.payment_amount = amount
                    schedule.outstanding = amount
                    schedule.discount = discount_amount
                    schedule.discount_type = payment_plan_discount[1]
                    schedule.discount_date = schedule.due_date
                elif payment_plan_discount and payment_plan_discount[1] == "Percentage":
                    discount_amount = payment_plan_discount[0]
                    amount = schedule.outstanding - payment_plan_discount[0]
                    schedule.payment_amount = amount
                    schedule.outstanding = amount
                    schedule.discount = discount_amount
                    schedule.discount_type = payment_plan_discount[1]
                    schedule.discount_date = schedule.due_date
                return discount_amount
        return 0
    except Exception as e:
        frappe.logger('pp_discount').exception(e)
        return 0
