import frappe
from frappe.utils.data import flt
import json
from edu_quality.public.py.utils import get_submitted_undertaking, get_undertaking_template

@frappe.whitelist()
def manual_payment(fee,term,data,payment_mode):
    try:
        data = frappe.parse_json(data)
        if term == "Deposit":
            filter = [["Payment Request","payment_term","is","not set"],["Payment Request","reference_name","=",fee],["Payment Request","docstatus","=",1]]
        else:
            filter = {'reference_name':fee,'payment_term':term,'docstatus':1}
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
def get_payment_details(fee, doctype, term):
    try:
        data = []
        company_wise =  json.loads(frappe.db.get_value(doctype,fee,"company_split"))[term]
        for i in company_wise:
            data.append({
                    "company": i,
                    "amount": flt(company_wise[i]['amount'],2),
                    "reference":""
                })
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
def get_unpaid_terms(fee, doctype):
    filters = [
        ["reference_doctype",'=',doctype],
        ["reference_name",'=',fee],
        ["status",'!=','Paid'],
        ['docstatus','=',1]
    ]
    terms = frappe.db.get_all("Payment Request",filters,"payment_term")
    result = []
    for term in terms:
        if not term.payment_term:
            result.append("Deposit")
        else:
            result.append(term.payment_term)
    fee_doc = frappe.get_doc(doctype,fee)
    is_deposit = False
    if fee_doc.component_split:
        component = json.loads(fee_doc.component_split)["Term 1"]
        is_deposit = component['is_deposit']
    if doctype =="Fees":
        filters = {"student": fee_doc.student,"program":fee_doc.program}
    else:
        filters = {"student": fee_doc.student,"program":fee_doc.next_program}

    if frappe.db.exists("Rules and Regulation Submission", filters,"name"):
        undertaking_accepted = True
    else:
        undertaking_accepted= False
    data = {"terms": result,"undertaking_accepted":undertaking_accepted,"undertaking_url": get_undertaking_template(is_deposit=is_deposit,fee=fee_doc)}
    return data
