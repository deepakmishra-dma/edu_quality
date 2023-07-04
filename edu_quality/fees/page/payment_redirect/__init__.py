import frappe 
import pickle
from frappe.utils.print_format import download_pdf

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
    fees = frappe.get_doc("Fees",payment_request.reference_name)
    breakup = []
    portion = 100
    if payment_request.payment_term:
        for schedule in fees.payment_schedule:
            if schedule.payment_term == payment_request.payment_term:
                portion = schedule.invoice_portion 

    for fee in fees.components:
        breakup.append({
            'fees_category': fee.fees_category,
            'amount':  frappe.utils.fmt_money(fee.amount *(portion/100), currency="INR")
            })
    return {
        'student_name': fees.student_name,
        'institution': fees.company,
        'due_date': fees.due_date,
        'class': fees.program,
        'student_id': fees.student,
        'due_amount': frappe.utils.fmt_money(fees.grand_total*(portion/100),currency="INR"),
        'payment_url': payment_url(payment_request,payment_method="UPI"),
        'status': payment_request.status,
        'receipt_url': frappe.utils.get_url() + "/api/method/edu_quality.fees.page.payment_redirect.payment_receipt?fees="+payment_request.reference_name,
        "breakup": breakup
    }


@cache_data(ttl=900)
@frappe.whitelist(allow_guest=True)
def payment_url(payment_request,payment_method="UPI"):
    return payment_request.get_payment_url(payment_method=payment_method)

@frappe.whitelist(allow_guest=True)
def payment_charge(**kwargs):
    charge = 0
    if frappe.db.exists("Payment Methods",{'method':kwargs.get('pm')}):
        charge = frappe.db.get_value("Payment Methods",{'method':kwargs.get('pm')},'charge')
    payment_request = frappe.get_value("Payment Request",{'payment_hash':kwargs.get('pr')},'name')
    payment_request = frappe.get_doc("Payment Request",payment_request)
    frappe.response['message'] = {'charge':charge,'url':payment_request.get_payment_url(payment_method=kwargs.get('pm'))}

@frappe.whitelist(allow_guest=True)
def payment_receipt(fees,category):
    try:
        company = frappe.db.get_value("Split Payment",category,"company")
        if not company:
            company = "Unique Educational and Sports Foundation"
        doc = frappe.db.get_value("Fee Receipt",{'fees':fees,"company":company},'name')
        if frappe.session.user == "Guest":
            frappe.local.login_manager.login_as("Administrator")
            pdf = download_pdf("Fee Receipt", doc)
            frappe.local.login_manager.login_as("Guest")
        else:
            pdf = download_pdf("Fee Receipt", doc)
        return pdf
    except Exception as e:
        frappe.logger("download").exception(e)
        return e
