import frappe 
from edu_quality.overrides import make_payment_request
from edu_quality.public.py.discount import only_deposit

@frappe.whitelist()
def separate_deposits(fees):
    try:
        fees = frappe.get_doc("Fees",fees)
        for schedule in fees.payment_schedule:
            if not "deposit" in schedule.description.lower():
                frappe.throw("The deposit is not combined in this case!")
            deposit_amount = get_deposit_amount(fees)
            if deposit_amount>0:
                term_amount = schedule.payment_amount - deposit_amount
                frappe.db.set_value("Payment Schedule",schedule.name,{
                    "payment_amount":term_amount,
                    "outstanding":term_amount,
                    "description": "Installment - 1"
                    })
                fees.reload()
                fees.update_split()
                if frappe.db.exists("Payment Request",{"reference_name":fees.name,"payment_term":schedule.payment_term}):
                    pr = frappe.get_doc("Payment Request",{"reference_name":fees.name,"payment_term":schedule.payment_term})
                    pr.cancel()

                only_deposit(fees)

                frappe.enqueue(
                    "edu_quality.public.py.student.create_payment_request",
                    fee=fees,
                    term = schedule.payment_term,
                    is_async=True,
                    queue="long",
                    timeout=1800,
                )
                return True
            break
    except Exception as e:
        frappe.logger('separation').exception(e)
        return False    
    
def get_deposit_amount(fees):
    initial_payment = 0
    for component in fees.components:
        if component.fee_type and component.fee_type!= "Regular":
            initial_payment = initial_payment +  component.amount
    return initial_payment