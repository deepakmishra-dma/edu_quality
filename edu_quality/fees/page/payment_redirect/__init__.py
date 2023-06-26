import frappe 
import pickle

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
    for fee in fees.components:
        breakup.append({
            'fees_category': fee.fees_category,
            'amount': fee.get_formatted('amount')
            })
    return {
        'student_name': fees.student_name,
        'institution': fees.company,
        'due_date': fees.due_date,
        'class': fees.program,
        'student_id': fees.student,
        'due_amount': fees.get_formatted('outstanding_amount'),
        'payment_url': payment_url(payment_request,payment_method="UPI"),
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
