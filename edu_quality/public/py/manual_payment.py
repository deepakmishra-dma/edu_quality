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
            frappe.db.set_value("Payment Request",filter,'mode_of_payment',payment_mode)
            pr = frappe.get_doc("Payment Request",filter)
            pr.set_as_paid()
            entries = frappe.get_all("Payment Entry", {"reference_no": pr.name},['name','company', 'party', 'paid_amount'])
            for entry in entries:
                for i in data:
                    if entry.company == i.get("company"):
                        reference_no = i.get("reference_number")
                        update_reference(reference_no, entry)

            frappe.response["message"] = "Manual Payment Done"
    except Exception as e:
        frappe.logger("manual").exception(e)
        frappe.response["message"] = "Manual Payment Failed"
        return e


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
        if term != 'Depsoit':
            for schedule in fee.payment_schedule:
                if schedule.payment_term == term:
                    portion  = schedule.invoice_portion
                    description = schedule.description
                    break 
            
        for component in fee.components:
            amount = component.custom_amount_after_discount or component.amount
            company = frappe.db.get_value("Fee Category",component.fees_category,"custom_company")
            if not company:
                company = "Unique Educational and Sports Foundation"
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