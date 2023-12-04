import json
import frappe 
import pickle
from frappe.utils.print_format import download_pdf
from edu_quality.public.py.utils import get_submitted_undertaking, get_undertaking_template

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

@frappe.whitelist(allow_guest=True)
def get_payment_details(**kwargs):
    payment_request = frappe.get_value("Payment Request",{'payment_hash': kwargs.get('doc')})
    payment_request = frappe.get_doc("Payment Request",payment_request)
    fees = frappe.get_doc(payment_request.reference_doctype, payment_request.reference_name)
    component = json.loads(fees.component_split)[payment_request.payment_term]
    breakup = component['breakup']
    due_date = component['due_date']
    is_deposit = component['is_deposit']
    if fees.doctype == "Fees":
        student_name = fees.student_name
        company = fees.company
    elif fees.doctype == "Fee Advance":
        student_name = frappe.db.get_value("Student", fees.student, "student_name")
        company = fees.institution

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
        "undertaking_url": get_undertaking_template(payment_request, is_deposit=is_deposit),
        "undertaking_accepted": get_submitted_undertaking(payment_request)
    }


@cache_data(ttl=900)
@frappe.whitelist(allow_guest=True)
def payment_url(payment_request,payment_method="UPI"):
    return payment_request.get_payment_url(payment_method=payment_method)

@frappe.whitelist(allow_guest=True)
def payment_charge(**kwargs):
    charge = 0
    payment_request = frappe.get_value("Payment Request",{'payment_hash':kwargs.get('pr')},'name')
    payment_request = frappe.get_doc("Payment Request",payment_request)
    frappe.response['message'] = {'charge':charge,'url':payment_request.get_payment_url(payment_method=kwargs.get('pm'))}

@frappe.whitelist(allow_guest=True)
def payment_receipt(payment_request,category):
    try:
        company = frappe.db.get_value("Fee Category",category,"custom_company")
        if not company:
            company = "Unique Educational and Sports Foundation"
        doc = frappe.db.get_value("Payment Entry",{'reference_no':payment_request,"company":company},'name')
        fee_name = frappe.db.get_value("Payment Request", payment_request, 'reference_name')
        program_name = frappe.db.get_value("Fees", fee_name, 'program')
        print_format = frappe.db.get_value("Program", program_name, 'print_format')
        letter_head = frappe.db.get_value("Program", program_name, 'letter_head')
        letter_head_doc = frappe.get_doc("Letter Head", letter_head)
        print_format_doc = frappe.get_doc("Print Format", print_format)
        if frappe.session.user == "Guest":
            frappe.local.login_manager.login_as("Administrator")
            pdf = download_pdf("Payment Entry", doc, format=print_format_doc, letterhead=letter_head_doc)
            frappe.local.login_manager.login_as("Guest")
        else:
            pdf = download_pdf("Payment Entry", doc)
        return pdf
    except Exception as e:
        frappe.logger("download").exception(e)
        return e
