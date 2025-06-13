from datetime import datetime
from edu_quality.overrides import make_payment_request
from edu_quality.public.py.payment_request import update_payment_request_after_discount
import frappe
from frappe.utils import today, getdate, flt
import json
from edu_quality.public.py.term import get_first_unpaid_term,get_last_term


def get_discount_applicable_term(dis):
    if dis.type == "Payment Plan":
        return -1
    return "All"

@frappe.whitelist()
def add_discount(fee_name, discount, fees=None, doctype="Fees"):
    try:
        discount_applied = False
        grand_discount_amount = 0
        if not fees:
            fees = frappe.get_doc(doctype, fee_name)
        dis = frappe.get_doc("Discount Configuration", discount)
        company = None
        for component in fees.components:
            if component.fees_category == dis.fee_category:
                update_breakups(dis,component,fees,term=get_discount_applicable_term(dis),update=1)
                fees.reload()
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
                            update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees, is_amount=True)
                            message = dis.name + " Discount applied successfully"
                            discount_applied = True
                            frappe.response['message'] = message
                        else:
                            grand_discount_amount = (component.amount * float(dis.discount)) / 100
                            discounted_amount = grand_discount_amount + component.custom_discount_amount
                            discount = calculate_discount(component.amount, discounted_amount)
                            amount = component.amount - discounted_amount
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
                        update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees, is_amount=True)
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
            if doctype == "Fees":
                update_total_discount_in_fees(fees)
                if dis.needs_admin_approval:
                    frappe.db.set_value("Fees",fee_name,"workflow_state","Pending")
                    # update_payment_plan_after_discount(fees, grand_discount_amount, apply_discount=True,dis=dis)
                else:
                    pass
                    # update_payment_plan_after_discount(fees, grand_discount_amount, apply_discount=True,dis=dis)
                fees.add_discount_entry(company, grand_discount_amount)
            elif doctype == "Fee Advance":
                pass
            fees.update_split()
            fees.reload()
            fees.save(ignore_permissions=True)
            update_payment_request_after_discount(fees)
    except Exception as e:
        frappe.logger('add_discount').exception(e)


@frappe.whitelist()
def remove_discount(fee_name, discount, update_payment_request=True, doctype="Fees",custom_payment_plan=0):
    try:
        frappe.logger('remove').exception('removed')
        discount_removed = False
        grand_discount_amount = 0
        fees = frappe.get_doc(doctype, fee_name)
        dis = frappe.get_doc("Discount Configuration", discount)
        company = None

        for component in fees.components:
            if component.custom_discounts:
                company = component.custom_company
                discount_list = get_discount_list(component.custom_discounts)
                if component.fees_category == dis.fee_category and discount in discount_list:
                    update_breakups(dis,component,fees,term=get_discount_applicable_term(dis),update=1,remove=1,custom=custom_payment_plan)
                    if dis.discount_amount:
                        grand_discount_amount = dis.discount_amount
                        amount = component.custom_amount_after_discount + grand_discount_amount
                        discount_amount = component.custom_discount_amount - grand_discount_amount
                        discount = calculate_discount(component.amount, discount_amount)
                        discount_list.remove(dis.name)
                        discount_name = ", ".join(discount_list)
                        # updating the data in the database
                        remove_and_update_component(component.name, discount_name, discount, discount_amount, grand_discount_amount, amount, fees, is_amount=True)
                        message = dis.name + " Discount removed successfully"
                        discount_removed = True
                        frappe.response['message'] = message
                    else:
                        grand_discount_amount = (component.amount * float(dis.discount)) / 100
                        amount = component.custom_amount_after_discount + grand_discount_amount
                        discount_amount = component.custom_discount_amount - grand_discount_amount
                        discount = calculate_discount(amount, discount_amount)
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
            if doctype == "Fees":
                # update_payment_plan_after_discount(fees, grand_discount_amount, apply_discount=False,dis=dis)
                fees.remove_discount_entry(company, grand_discount_amount)
            fees.update_split()
            fees.reload()
            fees.save(ignore_permissions=True)
            update_total_discount_in_fees(fees)
            if update_payment_request:
                update_payment_request_after_discount(fees)
    except Exception as e:
        frappe.logger('remove_dis').exception(e)


def update_total_discount_in_fees(fees):
    return
    try:
        frappe.db.set_value("Fees",fees.name,'total_discount',get_all_discounts(fees))
    except Exception as e:
        frappe.logger('custom').exception(e)



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
def update_component(component_name, discount_name, final_discount, discounted_amount, grand_discount_amount, amount, fees, is_amount=False):
    if is_amount and fees.doctype == "Fee Advance":
        discounted_amount -= grand_discount_amount
        invoice_portion = frappe.get_value("Payment Schedule", {"payment_term":fees.payment_term, "parent": fees.payment_plan}, "invoice_portion")
        grand_discount_amount = grand_discount_amount * invoice_portion / 100
        discounted_amount += grand_discount_amount
        if invoice_portion != 100:
            amount += grand_discount_amount

    fee_component_fields = {
        "custom_discounts": discount_name,
        "custom_discount_percentage": final_discount,
        "custom_discount_amount": discounted_amount,
        "custom_amount_after_discount": amount
    }
    frappe.db.set_value("Fee Component", component_name, fee_component_fields)

    if fees.doctype == "Fees":
        grand_total = fees.grand_total - grand_discount_amount
        fees_fields = {
            "grand_total": grand_total,
            "grand_total_in_words": str(frappe.utils.in_words(grand_total)).title(),
            "outstanding_amount": fees.outstanding_amount - grand_discount_amount,
            "total_discount": fees.total_discount + grand_discount_amount
        }
        frappe.db.set_value("Fees", fees.name, fees_fields)
    elif fees.doctype == "Fee Advance":
        fee_advance_fields = {
            "amount": fees.amount - grand_discount_amount,
            "outstanding_amount": fees.outstanding_amount - grand_discount_amount
        }
        frappe.db.set_value("Fee Advance", fees.name, fee_advance_fields)


def remove_and_update_component(component_name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees, is_amount=False):
    if is_amount and fees.doctype == "Fee Advance":
        discounted_amount += grand_discount_amount
        invoice_portion = frappe.get_value("Payment Schedule", {"payment_term":fees.payment_term, "parent": fees.payment_plan}, "invoice_portion")
        grand_discount_amount = grand_discount_amount * invoice_portion / 100
        discounted_amount -= grand_discount_amount
        if invoice_portion != 100:
            amount -= grand_discount_amount
            discount = calculate_discount(amount, discounted_amount)

    fee_component_update = {
        "custom_discounts": discount_name,
        "custom_discount_percentage": discount,
        "custom_amount_after_discount": amount,
        "custom_discount_amount": discounted_amount if discounted_amount else 0
    }
    frappe.db.set_value("Fee Component", component_name, fee_component_update)

    if fees.doctype == "Fees":
        grand_total = fees.grand_total + grand_discount_amount
        fees_update = {
            "grand_total": grand_total,
            "grand_total_in_words": str(frappe.utils.in_words(grand_total)).title(),
            "outstanding_amount": fees.outstanding_amount + grand_discount_amount,
            "total_discount": fees.total_discount - grand_discount_amount
        }
        frappe.db.set_value("Fees", fees.name, fees_update)
    elif fees.doctype == "Fee Advance":
        fee_advance_update = {
            "amount": fees.amount + grand_discount_amount,
            "outstanding_amount": fees.outstanding_amount + grand_discount_amount
        }
        frappe.db.set_value("Fee Advance", fees.name, fee_advance_update)


def get_label(fee_category):
    label = frappe.get_value("Fee Category", fee_category, "custom_label")
    if label:
        label = label.split("-")[0].strip()
    else:
        frappe.throw("Please set custom label for fee category {0}".format(fee_category))
    return label


def check_paid_advance(doc):
    filters = {"student": doc.student, "next_program":doc.program, "academic_year": doc.academic_year, "docstatus": 1}
    if frappe.db.exists("Fee Advance", filters):
        fee_advance = frappe.get_doc("Fee Advance", filters)
        if fee_advance.outstanding_amount>0:
            set_discount_to_fee(doc,fee_advance)
            # fee_advance.cancel()
            return False
        return True
    return False

def set_discount_to_fee(doc,fee_advance):
    discount_applied = get_one_time_discounts(fee_advance)
    for discount in discount_applied.keys():
        add_discount(doc.name, discount)
        # total_discount += discount_applied.get(discount)
    return

def get_one_time_discounts(doc):
    return {
        discount: component.custom_discount_amount
        for component in doc.components if component.custom_discounts
        for discount in map(str.lower, component.custom_discounts.split(", "))
        if "one time" in discount
    }

def payment_plan(doc, method=None):
    pe = frappe.get_doc("Program Enrollment", doc.program_enrollment)
    if pe.payment_plan is not None:
        doc.payment_plan = pe.payment_plan
    else:
        doc.payment_plan = frappe.db.get_value("Fee Schedule",doc.fee_schedule,'payment_plan')
    filters = {
        "student": doc.student,
        "next_program": doc.program,
        "academic_year": doc.academic_year,
        "docstatus": 1,
    }
    if frappe.db.exists("Fee Advance", filters):
        fee_advance = frappe.get_doc("Fee Advance", filters)
        doc.payment_plan = fee_advance.payment_plan
    doc.save()
    doc.reload()
    frappe.logger('log_p').exception(doc.payment_plan)
    if doc.payment_plan:
        pp = frappe.get_doc("Payment Plan",doc.payment_plan)
        doc.payment_schedule = []
        initial_payment = 0
        regular_amount = 0
        advance = check_paid_advance(doc)
        for component in doc.components:
            if component.fee_type and component.fee_type!= "Regular":
                initial_payment = initial_payment +  component.amount
            else:
                regular_amount += component.amount
        i=0
        for schedule in pp.payment_schedule:
            payment_amount = flt(regular_amount * schedule.invoice_portion/100,2)
            description = "Installment - " + str(i+1)
            if not advance:
                if i==0:
                    before_days = frappe.db.get_value("Fee Schedule",doc.fee_schedule,"create_payment_request_before")
                    today = datetime.today().date()
                    difference = schedule.due_date - today
                    if difference.days > before_days and initial_payment>0:
                            only_deposit(doc)
                    elif difference.days <= before_days:
                        #global check case
                        if not frappe.db.get_single_value("Fees Settings", "combine_deposit_and_due_fees"):
                            separate_links(doc,schedule.payment_term)
                        #student check
                        elif pe.do_not_combine_deposit_and_due_fees:
                            separate_links(doc,schedule.payment_term)
                        #combination case
                        else:
                            payment_amount = payment_amount + initial_payment
                            if initial_payment>0:
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
        doc.save()
        doc.reload()


def separate_links(doc,term):
    only_deposit(doc)
    frappe.enqueue(
        "edu_quality.public.py.student.create_payment_request",
        fee=doc,
        term = term,
        is_async=True,
        queue="long",
        timeout=1800,
    )



def only_deposit(doc):
    make_payment_request(
        party_type="Student",
        party=doc.student,
        dt="Fees",
        dn=doc.name,
        payment_request_type="Inward",
        is_deposit=True,
        recipient_id=frappe.db.get_value("Student",doc.student,'student_email_id'),
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
                label = component.label if component.label else get_label(component.fees_category)
                return {label:{component.fees_category:discount_amount}
}


def apply_time_based_discount(dis, component, fees):
    # if the discount is not already present
    update_breakups(dis, component, fees)
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
                if dis.get('type') == 'Referral':
                        pass
                    # if i == 0:
                    #     amount = schedule.outstanding - total_discount
                    #     frappe.db.set_value("Payment Schedule",schedule.name,"payment_amount",amount)
                    #     frappe.db.set_value("Payment Schedule",schedule.name,"outstanding",amount)
                        # dis_breakup = frappe.db.get_value("Payment Schedule",schedule.name,"discount_breakup")
                        # dis_breakup = json.loads(dis_breakup) if dis_breakup else None
                        # if dis_breakup:
                        #     if "Referral" in dis_breakup:
                        #         dis_breakup["Referral"]['discount_amount'] = dis_breakup["Referral"]['discount_amount'] + total_discount
                        #     else:
                        #         dis_breakup["Referral"] = {'discount_amount':total_discount}
                        # else:
                        #     dis_breakup = {"Referral":{'discount_amount':total_discount}}
                        # frappe.db.set_value("Payment Schedule",schedule.name,"discount_breakup",json.dumps(dis_breakup))
                        break

                elif dis.get('type') != "Payment Plan":
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
            update_breakups(dis, component, doc,term=-1)
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
        # other_discount = 0
        # for component in doc.components:
        #     if component.custom_discounts:
        #         discount_name = component.custom_discounts.lower()
        #         discount_amount = component.custom_discount_amount
        #         if discount_amount and "payment plan" not in discount_name:
        #             other_discount += component.custom_discount_amount

        # discount_applied = False
        # discount_amount = 0
        # for i, schedule in enumerate(doc.payment_schedule):
        #     if not discount_applied:
        #         amount = schedule.outstanding - other_discount
        #         schedule.payment_amount = amount
        #         schedule.outstanding = amount
        #         schedule.discount = other_discount
        #         schedule.discount_type = "Amount"
        #         schedule.discount_date = schedule.due_date
        #         discount_applied = True

        #     elif i == len(doc.payment_schedule) - 1:
        #         if payment_plan_discount and payment_plan_discount[1] == "Amount":
        #             discount_amount = payment_plan_discount[0]
        #             amount = schedule.outstanding - payment_plan_discount[0]
        #             schedule.payment_amount = amount
        #             schedule.outstanding = amount
        #             schedule.discount = discount_amount
        #             schedule.discount_type = payment_plan_discount[1]
        #             schedule.discount_date = schedule.due_date
        #         elif payment_plan_discount and payment_plan_discount[1] == "Percentage":
        #             discount_amount = payment_plan_discount[0]
        #             amount = schedule.outstanding - payment_plan_discount[0]
        #             schedule.payment_amount = amount
        #             schedule.outstanding = amount
        #             schedule.discount = discount_amount
        #             schedule.discount_type = payment_plan_discount[1]
        #             schedule.discount_date = schedule.due_date
        #         return discount_amount
        return 0
    except Exception as e:
        frappe.logger('pp_discount').exception(e)
        return 0


class AttributeDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def update_breakups(dis, component, fees, term="All", update=0,remove=0,custom=0):
    if fees.doctype == "Fee Advance":
        return
    try:
        if str(type(dis))=="<class 'dict'>":
            dis = AttributeDict(dis)

        if not dis.discount_amount and dis.discount!=None:
            dis.discount_amount = flt(dis.discount*component.amount/100,2)
        #update component

        discount_breakup = update_discount_breakup(component.amount, component.discount_breakup,
                                                            dis.discount,dis.discount_amount,dis.name,remove)
        if not update:
            component.discount_breakup = discount_breakup
        else:
            frappe.db.set_value("Fee Component",component.name,'discount_breakup',discount_breakup)

        #update_schedule
        if term == 1:
            term = get_first_unpaid_term(fees)
        elif term == -1:
            term = get_last_term(fees)

        if term !="All":
            for schedule in fees.payment_schedule:
                if term == schedule.payment_term:
                    discount_amount = dis.discount_amount
                    discount = flt((dis.discount_amount/schedule.payment_amount)*100,2)
                    if remove:
                        discount = flt(discount_amount/(schedule.payment_amount+discount_amount)*100,2)
                    discount_breakup = update_discount_breakup(schedule.payment_amount, schedule.discount_breakup,
                                                            discount,dis.discount_amount,dis.name,remove)
                    if remove:
                        discount_amount = 0-discount_amount
                    if custom:
                        discount_amount = 0
                    if not update:
                        schedule.discount_breakup = discount_breakup
                        schedule.payment_amount = schedule.payment_amount - discount_amount
                        schedule.outstanding = schedule.outstanding - discount_amount
                    else:
                        data = {
                                                'payment_amount': schedule.payment_amount - discount_amount,
                                                'outstanding': schedule.outstanding - discount_amount,
                                                'discount_breakup':discount_breakup
                                                }
                        frappe.db.set_value("Payment Schedule",schedule.name,data)
                    return
        else:
            for schedule in fees.payment_schedule:
                discount_amount = flt(dis.discount_amount * schedule.invoice_portion/100,2)
                discount = flt(discount_amount/schedule.payment_amount*100,2)
                if remove:
                    discount = flt(discount_amount/(schedule.payment_amount+discount_amount)*100,2)
                discount_breakup = update_discount_breakup(schedule.payment_amount, schedule.discount_breakup,
                                                                discount,discount_amount,dis.name,remove)
                # frappe.logger('breakup').exception(discount_amount)
                if remove:
                    discount_amount = 0-discount_amount
                if not update:
                    schedule.discount_breakup = discount_breakup
                    schedule.payment_amount = schedule.payment_amount - discount_amount
                    schedule.outstanding = schedule.outstanding - discount_amount
                else:
                    frappe.db.set_value("Payment Schedule",schedule.name,
                                            {
                                                'payment_amount': schedule.payment_amount - discount_amount,
                                                'outstanding': schedule.outstanding - discount_amount,
                                                'discount_breakup':discount_breakup
                                                })
        fees.reload()
    except Exception as e:
        frappe.logger("breakup").exception(e)




def update_discount_breakup(component_amount,discount_breakup,discount,discount_amount,discount_name,remove):
    """
    Update discount breakup details.

    Parameters:
    - component (object): The fee component object.
    - discount (object): The discount object.

    Returns:
    dict: Updated discount breakup details.
    """
    if  not discount_amount:
        discount_amount = flt(component_amount*discount/100,2)
    elif not discount:
        discount = flt((abs(discount_amount)/component_amount)*100,2)

    breakup = json.loads(discount_breakup) if discount_breakup else {}
    if breakup.get(discount_name):
        if not remove:
            breakup[discount_name]['discount_amount'] += discount_amount
            if breakup[discount_name].get('discount_percentage'):
                breakup[discount_name]['discount_percentage'] += discount
            else:
                breakup[discount_name]['discount_percentage'] = discount
        else:
            breakup[discount_name]['discount_amount'] -= discount_amount
            if breakup[discount_name].get('discount_percentage'):
                breakup[discount_name]['discount_percentage'] -= discount
            else:
                breakup[discount_name]['discount_percentage'] = discount

    else:
        if not remove:
            breakup[discount_name] = {"discount_amount": discount_amount, "discount_percentage": discount}
        else:
            pass
            # breakup[discount_name] = {"discount_amount": -discount_amount, "discount_percentage": -discount}


    return json.dumps(breakup)


def update_breakup_after_pp_change(fees):
    return
    for component in fees.components:
        breakup = json.loads(component.discount_breakup) if component.discount_breakup else None
        if not breakup:
            continue
        for dis in breakup:
            if dis == 'Referral':
                term = get_first_unpaid_term(fees)
            elif "Payment Plan" in dis:
                term = get_last_term(fees)
            else:
                term = "All"
            for schedule in fees.payment_schedule:
                if term == schedule.payment_term:
                    discount_amount = breakup[dis]['discount_amount']
                    discount = flt((discount_amount/schedule.payment_amount)*100,2)
                    new_breakup = update_discount_breakup(schedule.payment_amount, schedule.discount_breakup,
                                                                discount,discount_amount,dis,0)
                    frappe.db.set_value("Payment Schedule",schedule.name,{'discount_breakup':new_breakup})

                    fees.reload()
                elif term == 'All':
                    discount_amount = flt(breakup[dis]['discount_amount'] * schedule.invoice_portion/100,2)
                    discount = flt(discount_amount/schedule.payment_amount*100,2)
                    new_breakup = update_discount_breakup(schedule.payment_amount, schedule.discount_breakup,
                                                                discount,discount_amount,dis,0)
                    frappe.db.set_value("Payment Schedule",schedule.name,{'discount_breakup':new_breakup})
                    fees.reload()
    fees.update_split()