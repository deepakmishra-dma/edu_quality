import frappe 

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
        'payment_url': payment_request.get_payment_url()
    }