import frappe 
import json
from frappe.utils import flt


def generate_split_payment(fees,update=0):
    """
        fees: Fees or Fee Advance Doctype
        update: 0 or 1
        returns: {
                    "Term 1": {"RegistrationFeesFursungiPrimary": 90345.0, "KAPIL": 40331.0}, 
                    "Term 2": {"KAPIL": 37417.0, "RegistrationFeesFursungiPrimary": 20845.0}, 
                    "Deposit": {"RegistrationFeesFursungiPrimary": 69500.0}
                }
    """
    if update:
        fees.reload()
    split_payment = {}
    company_wise = {}
    component_wise = {}

    if fees.doctype == "Fees":
        case = check_deposit_combination(fees)  
        if case == 1:
            split_payment["Deposit"],company_wise["Deposit"],cw = get_split(fees,100,case,apply_deposit=0)
            component_wise["Deposit"] = {
                "due_date": None,
                "breakup": cw
            }
            case = 0

        # case 0 - no deposit
        for schedule in fees.payment_schedule:
            apply_deposit = 0
            if case == 2:
                if "deposit" in schedule.description.lower():
                    apply_deposit = 1
            split_payment[schedule.payment_term],company_wise[schedule.payment_term],cw = get_split(fees,schedule,case,apply_deposit=apply_deposit)
            component_wise[schedule.payment_term] = {
                "due_date": str(schedule.due_date),
                "breakup": cw,
                "is_deposit": apply_deposit
                }
            total = 0
            for i in split_payment[schedule.payment_term]:
                total += split_payment[schedule.payment_term][i]
            if schedule.payment_amount != total:
                if update:
                    frappe.db.set_value("Payment Schedule", schedule.name, 'payment_amount',total)
                    frappe.db.set_value("Payment Schedule", schedule.name, 'outstanding',total)
                else:
                    schedule.payment_amount = total
                    schedule.outstanding = total
            
    elif fees.doctype == "Fee Advance":
        term = fees.payment_term
        split_payment[term], company_wise[term], components = get_split_fee_advance(fees)
        component_wise[term] = {
            "due_date": str(fees.due_date),
            "breakup": components,
            "is_deposit": False
        }

    if update:
        frappe.db.set_value("Fees",fees.name,'split_payments',json.dumps(split_payment))
        frappe.db.set_value("Fees",fees.name,'company_split',json.dumps(company_wise))
        frappe.db.set_value("Fees",fees.name,'component_split',json.dumps(component_wise))
    else:
        fees.split_payments = json.dumps(split_payment)
        fees.company_split = json.dumps(company_wise)
        fees.component_split = json.dumps(component_wise)
    return split_payment, company_wise, component_wise


def get_split(fees, schedule, case=0,apply_deposit=0):
    try:
        split = {}
        company_wise = {}
        component_wise = []
        for component in fees.components:
            if case == 1:
                if component.fee_type == "Regular":
                    continue
                portion = 100
            else:
                portion = schedule.invoice_portion

            amount = flt(component.amount * portion/100,2)
            if component.fee_type != "Regular":
                amount = component.amount
            discount_amount = 0
            if case != 1:
                if schedule.discount_breakup:
                    schedule_breakup = json.loads(schedule.discount_breakup)
                    component_breakup = json.loads(component.discount_breakup) if component.discount_breakup else {}
                    for discount in schedule_breakup:
                        if discount in component_breakup:
                            amount -= schedule_breakup[discount]['discount_amount']
                            discount_amount += schedule_breakup[discount]['discount_amount']

            if case == 2 and component.fee_type !='Regular' and apply_deposit==0:
                continue          
            elif case==0 and component.fee_type !="Regular":
                continue

            label = component.label
            if label:
                label = label.split("-")[0].strip()

            split[label] = split.get(label, 0) + amount
            paid_to = frappe.db.get_value("Fee Category",component.fees_category,'custom_account') 
            paid_from = frappe.db.get_value("Company",component.custom_company,"default_receivable_account")
            cost_center = frappe.get_value(
                "Cost Center", {"company": component.custom_company}, ["name"]
            )

            component_wise.append({
                "fees_category":component.fees_category,
                "company": component.custom_company,
                "amount": amount,   
                "discount_amount":discount_amount
                })

            if component.custom_company in company_wise:
                company_wise[component.custom_company]['amount'] += amount 
            else:
                company_wise_breakup = {
                    'amount': amount,
                    'paid_from': paid_from,
                    'paid_to': paid_to,
                    'cost_center': cost_center
                }
                company_wise[component.custom_company] = company_wise_breakup
        return split,company_wise, component_wise
    except Exception as e:
        frappe.logger('split').exception(e)


def check_deposit_combination(fees):
    deposit = 0
    for component in fees.components:
        if component.fee_type and component.fee_type!="Regular":
            deposit=1
            break 
    for schedule in fees.payment_schedule:
        if "deposit" in schedule.description.lower():
            deposit = 2
            break 
    return deposit


def get_split_fee_advance(fees):
    try:
        split = {}
        company_wise = {}
        component_wise = []
        for component in fees.components:
            label = component.label
            amount = component.amount
            if label:
                label = label.split("-")[0].strip()

            split[label] = split.get(label, 0) + amount
            paid_to = frappe.db.get_value("Fee Category",component.fees_category,'custom_account') 
            paid_from = frappe.db.get_value("Company",component.custom_company,"default_receivable_account")
            cost_center = frappe.get_value(
                "Cost Center", {"company": component.custom_company}, ["name"]
            )

            component_wise.append({
                "fees_category":component.fees_category,
                "company": component.custom_company,
                "amount": amount,   
                "discount_amount":0
                })

            if component.custom_company in company_wise:
                company_wise[component.custom_company]['amount'] += amount 
            else:
                company_wise_breakup = {
                    'amount': amount,
                    'paid_from': paid_from,
                    'paid_to': paid_to,
                    'cost_center': cost_center
                }
                company_wise[component.custom_company] = company_wise_breakup
        return split,company_wise, component_wise
    except Exception as e:
        frappe.logger('split').exception(e)