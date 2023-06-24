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

@frappe.whitelist()
def get_payment_details(**kwargs):
    payment_request = frappe.get_doc("Payment Request",kwargs.get("doc"))
    fees = frappe.get_doc("Fees",payment_request.reference_name)
    return {
        'student_name': fees.student_name,
        'institution': fees.company,
        'due_date': fees.due_date,
        'class': fees.program,
        'student_id': fees.student,
        'due_amount': fees.outstanding_amount,
        'payment_url': "url",#payment_request.get_payment_url(),
        "breakup": fees.components
    }


@cache_data(ttl=900)
def payment_url(payment_request):
    return payment_request.get_payment_url()


