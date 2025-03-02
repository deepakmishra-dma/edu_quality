import json
import frappe 
import pickle
from frappe.utils.print_format import download_pdf
from edu_quality.public.py.utils import get_submitted_undertaking, get_undertaking_template
from frappe.utils.data import flt 
import json 


def cache_data(ttl):
    def cache_processor(func):
        def check_cache_exists(*args, **kwargs):
            rs = frappe.cache()
            key = "payment_url"
            result = rs.get_value(key)
            if result:
                return pickle.loads(result)
            else:
                data = func(*args, **kwargs)
                rs.set_value(key, pickle.dumps(data), expires_in_sec=ttl)
                return data
        return check_cache_exists
    return cache_processor


def get_breakup(fees,term):
    breakups = []
    deposit=0
    schecule_breakup = {} 
    portion = 100
    if fees.doctype == 'Fees':
        for schedule in fees.payment_schedule:
            if schedule.payment_term == term:
                portion = schedule.invoice_portion 
                if 'deposit' in schedule.description.lower():
                    deposit = 1 
                schecule_breakup = json.loads(schedule.discount_breakup) if schedule.discount_breakup else {}

    for component in fees.components:
        breakup = []
        amount = flt(component.amount*portion/100,2) 
        if fees.doctype == 'Fees':
            if not deposit and component.fee_type != 'Regular':
                continue
            elif deposit and component.fee_type != 'Regular':
                amount = flt(component.amount,2)
        company = component.custom_company
        if component.discount_breakup:
            component_breakup = json.loads(component.discount_breakup) if component.discount_breakup else {}
            for dis in component_breakup:
                if dis in schecule_breakup:
                    dis_amount = flt(schecule_breakup[dis]['discount_amount'],2)
                    breakup.append({
                    'fees_category': "Discount- " + dis,
                    'amount':  frappe.utils.fmt_money(0-dis_amount, currency="INR"),
                    'company': company
                })
        display_name = component.fees_category
        if frappe.db.exists("Fee Category",component.fees_category):
            display_name = frappe.db.get_value("Fee Category",component.fees_category,'display_name') or component.fees_category
        breakup = [{
                'fees_category': display_name,
                'amount':  frappe.utils.fmt_money(amount, currency="INR"),
                'company': company
            }] + breakup
        breakups = breakups + breakup
    return breakups

@frappe.whitelist(allow_guest=True)
def get_payment_details(**kwargs):
    payment_request = frappe.get_value("Payment Request",{'payment_hash': kwargs.get('doc')})
    payment_request = frappe.get_doc("Payment Request",payment_request)
    if payment_request.docstatus == 2:
        if frappe.db.exists("Payment Request",{
            "reference_name":payment_request.reference_name,
            "payment_term":payment_request.payment_term,
            "status":"Initiated"
            }):
                request = frappe.db.get_value("Payment Request",{
                "reference_name":payment_request.reference_name,
                "payment_term":payment_request.payment_term,
                "status":"Initiated"
                },"payment_hash")
                return {'redirect': frappe.utils.get_url()+"/payment?payment_request="+request}
        return frappe.throw("The payment link is invalidated or cancelled! Please check email for new link or contact the school!")
    fees = frappe.get_doc(payment_request.reference_doctype, payment_request.reference_name)
    breakup = []
    if payment_request.payment_term:
        component = json.loads(fees.component_split)[payment_request.payment_term]
        breakup = get_breakup(fees,payment_request.payment_term)
        if fees.doctype == "Fees":
            due_date = frappe.get_value("Payment Schedule",{'parent':fees.name,'payment_term':payment_request.payment_term},'due_date')
        elif fees.doctype == "Fee Advance":
            due_date = fees.due_date
        is_deposit = component['is_deposit']
        if fees.doctype == "Fees":
            first_name = frappe.db.get_value("Student", fees.student, "first_name")
            last_name = frappe.db.get_value("Student", fees.student, "last_name")
            student_name = f"{first_name} {last_name or ''}"
            company = fees.company
        elif fees.doctype == "Fee Advance":
            first_name = frappe.db.get_value("Student", fees.student, "first_name")
            last_name = frappe.db.get_value("Student", fees.student, "last_name")
            student_name = f"{first_name} {last_name or ''}"
            company = fees.company
    else:
        first_name = frappe.db.get_value("Student", fees.student, "first_name")
        last_name = frappe.db.get_value("Student", fees.student, "last_name")
        student_name = f"{first_name} {last_name or ''}"
        due_date = fees.due_date
        for fee in fees.components:
            fee_type = frappe.db.get_value("Fee Category",fee.fees_category,"type")
            amount = fee.custom_amount_after_discount or fee.amount
            if frappe.db.exists("Fee Category",fee.fees_category):
                company = frappe.db.get_value("Fee Category",fee.fees_category,"custom_company")
            else:
                company = fees.company
                
            if fee_type != "Regular":
                display_name = fee.fees_category
                if frappe.db.exists("Fee Category",fee.fees_category):
                    display_name = frappe.db.get_value("Fee Category",fee.fees_category,'display_name') or fee.fees_category
                breakup.append({
                    'fees_category': display_name,
                    'amount':  frappe.utils.fmt_money(amount, currency="INR"),
                    'company': company
                })
                is_deposit = True

    return {
        'student_name': student_name,
        'institution': company,
        'due_date': due_date,
        'class': fees.program,
        'student_id': fees.student,
        'due_amount': frappe.utils.fmt_money(payment_request.grand_total,currency="INR"),
        'payment_url': payment_url(payment_request,payment_method="UPI"),
        'status': payment_request.status,
        'receipt_url': frappe.utils.get_url() + "/api/method/edu_quality.fees.page.payment_redirect.payment_receipt?payment_request="+payment_request.name,
        "breakup": breakup,
        "discounts": get_discounts(fees),
        "term": payment_request.payment_term or "Deposit",
        "undertaking_url": get_undertaking_template(payment_request, is_deposit=is_deposit),
        "undertaking_accepted": get_submitted_undertaking(payment_request)
    }


def get_discounts(fees):
    referral_discount = 0
    other_discount = 0
    referral_discount_company = None
    other_discount_company = None
    if fees.doctype == "Fees":
        pass
    if fees.doctype == "Fee Advance":
        for component in fees.components:
            if component.fees_category in ["Tuition Fee", 'Tuition Fee (KG)']:
                referral_discount_company = component.custom_company
            if component.custom_discounts:
                if component.custom_company == fees.company:
                    other_discount += component.custom_discount_amount
                    other_discount_company = component.custom_company
                    if "Referral" in component.custom_discounts:
                        other_discount -= fees.referral_amount
        if fees.referral_amount:
            referral_discount += fees.referral_amount
    return {"referral_discount": referral_discount, "other_discount":other_discount, "referral_discount_company": referral_discount_company, "other_discount_company": other_discount_company}



@frappe.whitelist(allow_guest=True)
def payment_url(payment_request,payment_method="UPI"):
    try:
        return payment_request.get_payment_url(payment_method=payment_method)
    except Exception as e:
        frappe.logger('payment_er').exception(e)

@frappe.whitelist(allow_guest=True)
def payment_charge(**kwargs):
    charge = 0
    payment_request = frappe.get_value("Payment Request",{'payment_hash':kwargs.get('pr')},'name')
    payment_request = frappe.get_doc("Payment Request",payment_request)
    frappe.response['message'] = {'charge':charge,'url':payment_request.get_payment_url(payment_method=kwargs.get('pm'))}

@frappe.whitelist(allow_guest=True)
def payment_receipt(payment_request, category):
    try:
        company = get_company(payment_request, category)

        payment_entry = frappe.get_value("Payment Entry", {'payment_request': payment_request, "company": company}, ['name'])

        letter_head = get_letter_head(payment_request, category)

        print_format = frappe.get_value("Fees Settings", None, "print_format")

        if frappe.session.user == "Guest":
            frappe.set_user("Administrator")
            pdf = download_pdf("Payment Entry", payment_entry, format=print_format, letterhead=letter_head)
            frappe.set_user("Guest")
        else:
            pdf = download_pdf("Payment Entry", payment_entry, format=print_format, letterhead=letter_head)
        return pdf
    except Exception as e:
        frappe.logger("download").exception(e)
        return e


def get_company(payment_request, category):
    """
    Returns the company associated with a Fee Category or Fees or Fee Advance.
    it will return the company associated with the Fee Category if it exists.
    If not, it will return the company associated with the Fees or Fee Advance.
    If not, it will return the default company of the user.
    """
    default_company = frappe.defaults.get_user_default("Company")
    doctype, fee_name = frappe.get_value("Payment Request", payment_request, ['reference_doctype', 'reference_name'])
    fee = frappe.get_doc(doctype, fee_name)
    company = next((component.custom_company for component in fee.components if component.fees_category == category), None)
    return company or default_company


def get_letter_head(payment_request, category):
    """
    Returns the letter head based on the payment request and category.
    """
    doctype, fee_name = frappe.get_value("Payment Request", payment_request, ['reference_doctype', 'reference_name'])
    fee = frappe.get_doc(doctype, fee_name)
    for component in fee.components:
        if component.fees_category == category:
            letter_head = None
            if component.school:
                letter_head = frappe.get_value("School", component.school, 'letter_head')
            elif component.custom_company:
                letter_head = frappe.get_value("Company", component.custom_company, 'default_letter_head')
            if letter_head:
                return letter_head
    return None
