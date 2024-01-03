import frappe
from frappe.utils.data import flt

@frappe.whitelist()
def manual_payment(fee,term,data,payment_mode):
    try:
        data = frappe.parse_json(data)
        if term == "Deposit":
            filter = [["Payment Request","payment_term","is","not set"],["Payment Request","reference_name","=",fee]]
        else:
            filter = {'reference_name':fee,'payment_term':term}
        if frappe.db.exists("Payment Request",filter):
            frappe.enqueue(set_as_paid,queue='long',filter=filter,data=data,payment_mode=payment_mode)
    except Exception as e:
        frappe.logger('manual').exception(e)
        return e
    
def set_as_paid(filter,data,payment_mode):
    frappe.db.set_value("Payment Request",filter,'mode_of_payment',payment_mode)
    pr = frappe.get_doc("Payment Request",filter)
    pr.save()
    pr.set_as_paid()
    entries = frappe.get_all("Payment Entry", {"reference_no": pr.name},['name','company', 'party', 'paid_amount'])
    for entry in entries:
        for i in data:
            if entry.company == i.get("company"):
                reference_no = i.get("reference_number")
                update_reference(reference_no, entry)



def update_reference(reference_no, entry):
    date = frappe.utils.nowdate()
    remarks = f"Amount INR {entry.paid_amount} received from {entry.party} Transaction reference no {reference_no} dated {date}"
    frappe.db.set_value("Payment Entry", entry.name, "reference_no", reference_no)
    frappe.db.set_value("Payment Entry", entry.name, "reference_date", date)
    frappe.db.set_value("Payment Entry", entry.name, "remarks", remarks)


@frappe.whitelist()
def get_payment_details(fee,term):
    try:
        fee = frappe.get_doc("Fees",fee)
        data = []
        portion = 100
        description = ""
        term_count = 0
        if term != 'Depsoit':
            for schedule in fee.payment_schedule:
                if schedule.payment_term == term:
                    portion  = schedule.invoice_portion
                    description = schedule.description
                    term_count+=1
                    break 
        last_term = 1 if len(fee.payment_schedule) == term_count else 0
        for component in fee.components:
            amount = component.custom_amount_after_discount or component.amount
            if component.custom_discounts and "payment plan" in component.custom_discounts.lower():
                pp_amount,pp_percent = frappe.get_value("Discount Configuration",{'payment_plan':fee.payment_plan},['discount_amount','discount'])
                if not last_term:
                    if not pp_amount:
                        pp_amount = flt(component.amount *(pp_percent/100),2)
                    if component.custom_discount_amount != pp_amount:
                        amount = component.amount - pp_amount
                    else: 
                        amount = component.amount
            company = frappe.db.get_value("Fee Category",component.fees_category,"custom_company")
            if not company:
                company = "Unique Educational and Sports Foundation"
            entry = {
                "company": company,
                "amount": flt(0,2),
                "reference":""
            }
            if component.fee_type !='Regular' and term == 'Deposit':
                entry ={
                    "company": company,
                    "amount": flt(amount,2),
                    "reference":""
                }
            elif term != 'Deposit':
                if component.fee_type!='Regular' and 'deposit' in description:
                    entry ={
                    "company": company,
                    "amount": flt(amount,2),
                    "reference":""
                    }
                elif component.fee_type == "Regular":
                    entry = {
                    "company": company,
                    "amount": flt(amount *(portion/100),2),
                    "reference":""
                    }
            if not entry['amount'] == 0:
                data = company_wise(data,entry)
        return data
    except Exception as e:
        frappe.logger('manual').exception(e)


def company_wise(data, component):
    f=0
    for i in data:
        if i.get('company') == component.get('company'):
            i['amount'] += component.get('amount')
            f=1
            break
    if f==0:
        data.append(component)
    return data


@frappe.whitelist()
def get_unpaid_terms(fee):
    terms = frappe.db.get_all("Payment Request",{'reference_name':fee},"payment_term")
    result = []
    for term in terms:
        if not term.payment_term:
            result.append("Deposit")
        else:
            result.append(term.payment_term)
    return result
