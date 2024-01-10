import frappe 
from edu_quality.public.py.discount import remove_discount
from datetime import datetime
from edu_quality.public.py.discount import add_discount, get_all_discounts



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
def change_payment_plan(payment_plan,fee_name):
    doc = frappe.get_doc("Fees", fee_name)

    for ps in doc.payment_schedule:
        if ps.outstanding == 0:
            frappe.throw(f"Cannot Change Payment Plan As {ps.payment_term} is already Paid!")
    
    remove_payment_plan_discount(doc)
    update_payment_plan(payment_plan,doc)

def remove_payment_plan_discount(doc):
    discount_configs = frappe.get_all("Discount Configuration",
        filters={"payment_plan": doc.payment_plan, "fee_structure": doc.fee_structure},
        fields=["name", "fee_category"])
    for component in doc.components:
        for discount_config in discount_configs:
            if discount_config.fee_category == component.fees_category:
                remove_discount(doc.name, discount_config.name, update_payment_request=True)
                frappe.response['message'] = f"{discount_config.name} Discount removed successfully"
                break

@frappe.whitelist()
def update_payment_plan(payment_plan, doc):
    deposit,apply_deposit = get_deposit_amount(doc)
    payment_plan = frappe.get_doc("Payment Plan", payment_plan)
    discount = update_payplan_discount(doc, payment_plan)
    if discount:
        add_discount(doc.name, discount[1].name)
        discount_amount = discount[0]
    doc.total_discount = get_all_discounts(doc)
    doc.payment_schedule = []

    other_amounts = doc.grand_total - deposit
    for i, ps in enumerate(payment_plan.payment_schedule):
        description = f"Installment {i+1}"
        amount = (ps.invoice_portion * other_amounts) / 100
        if i == 0 and apply_deposit:
            description += " and Deposit/Registration"
            amount += deposit
        if i == len(payment_plan.payment_schedule)-1 and discount:
            amount -= discount_amount
        doc.append("payment_schedule",{
            'payment_term':ps.payment_term,
            'description': description,
            'invoice_portion': ps.invoice_portion,
            'payment_amount':amount,
            'outstanding':amount,
            'due_date':ps.due_date
        })
    doc.payment_plan = payment_plan.name
    doc.save(ignore_permissions=True)
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