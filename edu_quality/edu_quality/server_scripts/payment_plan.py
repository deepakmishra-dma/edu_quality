import frappe 
from edu_quality.public.py.discount import remove_discount
from datetime import datetime
from edu_quality.public.py.discount import add_discount, get_all_discounts
import json
from frappe.utils import flt
from edu_quality.public.py.payment_request import update_payment_request_after_discount
from edu_quality.fees.doctype.fee_advance.fee_advance import get_percent, get_components

def get_deposit_amount(fees):
    apply_deposit = 0
    for schedule in fees.payment_schedule:
        if 'deposit' in schedule.description.lower():
            apply_deposit = 1

    deposits = 0
    for component in fees.components:
        if component.fee_type !='Regular':
            deposits += component.amount 
    return deposits,apply_deposit



@frappe.whitelist()
def change_payment_plan(payment_plan, doctype, fee_name):
    if doctype == "Fees":
        doc = frappe.get_doc("Fees", fee_name)

        for ps in doc.payment_schedule:
            if ps.outstanding == 0:
                frappe.throw(f"Cannot Change Payment Plan As {ps.payment_term} is already Paid!")

        for component in doc.components:
            discounts = component.custom_discounts.split(',') if component.custom_discounts else []
            for dis in discounts:
                if not dis or dis == '' or dis == ' ':
                    continue
                if "Referral" not in dis or "Payment Plan" not in dis:
                    frappe.throw(f"Cannot Change Payment Plan! remove {dis} to modify payment plan!")
        
        remove_payment_plan_discount(doc)
        doc.reload()
        update_payment_plan(payment_plan,doc)
        update_payment_request_after_discount(doc)
    
    elif doctype == "Fee Advance":
        doc = frappe.get_doc("Fee Advance", fee_name)
        percent = get_percent(doc.payment_term, payment_plan)
        if doc.outstanding_amount == 0:
            frappe.throw(f"Cannot Change Payment Plan As the Fee Advance is already Paid!")

        components, amount = get_components(doc.fee_structure, percent, doc.is_rte)
        doc.payment_plan = payment_plan
        doc.amount = amount
        doc.outstanding_amount = amount
        doc.components = []
        doc.remove_all_discount_entries()
        for component in components:
            doc.append('components', component)
        doc.make_gl_entries()  
        doc.save(ignore_permissions=True)
        frappe.response["message"] = "Payment Plan Updated Successfully!"
        update_payment_request_after_discount(doc)

def remove_payment_plan_discount(doc,custom_payment_plan=0):
    discount_configs = frappe.get_all("Discount Configuration",
        filters={"payment_plan": doc.payment_plan, "fee_structure": doc.fee_structure},
        fields=["name", "fee_category"])
    for component in doc.components:
        for discount_config in discount_configs:
            if discount_config.fee_category == component.fees_category:
                remove_discount(doc.name, discount_config.name, update_payment_request=True, custom_payment_plan=custom_payment_plan)
                frappe.response['message'] = f"{discount_config.name} Discount removed successfully"
                return

def get_term_wise_discounts(fees,payment_plan):
    discounts = {}
    terms = [schedule.payment_term for schedule in payment_plan.payment_schedule]
    for component in fees.components:
        if component.discount_breakup:
            discount = json.loads(component.discount_breakup)
            for dis in discount:
                if "payment" not in str(dis).lower():
                    if dis == "Referral":
                        for schedule in payment_plan.payment_schedule:
                            if schedule.outstanding!=0:
                                discounts[schedule.payment_term] = {
                                    dis: discount[dis]
                                }
                    else:
                        for schedule in payment_plan.payment_schedule:
                            discounts[schedule.payment_term] = {
                                    dis: {
                                        "discount_amount": flt(discount[dis]["discount_amount"] * schedule.invoice_portion/100,2)
                                    }
                                }
    return discounts
                    
    


@frappe.whitelist()
def update_payment_plan(payment_plan, doc):
    deposit,apply_deposit = get_deposit_amount(doc)
    payment_plan = frappe.get_doc("Payment Plan", payment_plan)
    term_discounts = get_term_wise_discounts(doc,payment_plan)
    doc.payment_plan = payment_plan.name
    doc.payment_schedule = []
   
    other_amounts = doc.grand_total - deposit
    for i, ps in enumerate(payment_plan.payment_schedule):
        description = f"Installment {i+1}"
        amount = (ps.invoice_portion * other_amounts) / 100
        if i == 0 and apply_deposit:
            description += " and Deposit/Registration"
            amount += deposit
        # if i == len(payment_plan.payment_schedule)-1 and discount:
        #     amount -= discount_amount
        breakup = term_discounts.get(ps.payment_term,{})
        frappe.logger('modify').exception(breakup)
        doc.append("payment_schedule",{
            'payment_term':ps.payment_term,
            'description': description,
            'invoice_portion': ps.invoice_portion,
            'payment_amount':amount,
            'outstanding':amount,
            'due_date':ps.due_date,
            'discount_breakup': json.dumps(breakup)
        })
    doc.total_discount = get_all_discounts(doc)
    doc.save(ignore_permissions=True)
    discount = update_payplan_discount(doc, payment_plan)
    if discount:
        add_discount(doc.name, discount[1].name,fees=doc)
        doc.reload()
        discount_amount = discount[0]
    doc.reload()
    doc.total_discount = get_all_discounts(doc)
    doc.save(ignore_permissions=True)
    doc.update_split()
    


    
    frappe.response["message"] = "Payment Plan Updated Successfully!"


def update_payplan_discount(doc, payment_plan):
    """
    update time based discount and referal discount in the payment schedule
    """
    for ps in payment_plan.payment_schedule:
        if ps.due_date < datetime.today().date():
            frappe.msgprint("Cannot Apply new Payment Plan Discount As Due Date is Passed!")
            return
        
    for component in doc.components:
        dis_filter = {"payment_plan": payment_plan.name, "fee_structure":doc.fee_structure, "fee_category": component.fees_category, "enabled":1}
        if frappe.db.exists("Discount Configuration", dis_filter):
            dis = frappe.get_doc("Discount Configuration", dis_filter)
            if dis.discount_amount:
                return dis.discount_amount, dis
            else:
                discount_amount = (component.amount * float(dis.discount)) / 100
                return discount_amount, dis
    return None