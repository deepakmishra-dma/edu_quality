import frappe
import json
from dateutil.parser import parse

@frappe.whitelist()
def create_payment_plans(**kwargs):
    try:
        submission_data = json.loads(kwargs.get("data"))
        plan_name = submission_data['planName']
        academic_year = submission_data['academicYear']
        school = submission_data['school']
        payment_terms = submission_data['paymentTerms']

        # Group payment terms by class
        class_payment_terms = {}  # Dictionary to store class-wise payment terms
        for term in payment_terms:
            class_name = term['class']
            if class_name not in class_payment_terms:
                class_payment_terms[class_name] = []
            class_payment_terms[class_name].append(term)
        
        for class_name, class_terms in class_payment_terms.items():
            fee_structure_name = frappe.get_value("Fee Structure", {
                "academic_year": academic_year,
                "school": school,
                "program": class_name
            }, "name")
            
            if not fee_structure_name:
                frappe.throw("Fee Structure not found for this class " + str(class_name))
                return False
            
            existing_payment_plan = frappe.get_all("Payment Plan", {
                "academic_year": academic_year,
                "school": school,
                "program": class_name
            }, ["name"])
            
            if existing_payment_plan:
                for plan in existing_payment_plan:
                    existing_payment_plan_doc = frappe.get_doc("Payment Plan", plan.name)
                    existing_schedule = existing_payment_plan_doc.payment_schedule
                    if len(existing_schedule) == len(class_terms):
                        # Compare payment terms, due dates, and invoice portions
                        is_identical = all(
                            term['paymentTerm'] == existing_term.payment_term and
                            term['invoicePortion'] == existing_term.invoice_portion
                            for term, existing_term in zip(class_terms, existing_schedule)
                        )
                        if is_identical:
                            frappe.throw("Identical Payment Plan already exists for this class " + str(class_name))
                            return False
            formatted_payment_plan = get_formatted_payment_plan(submission_data)
            pay_plan_name = plan_name+"-("+formatted_payment_plan[class_name]+")"
            payment_plan = frappe.get_doc({
                "doctype": "Payment Plan",
                "plan_name": pay_plan_name,
                "academic_year": academic_year,
                "school": school,
                "program": class_name,
                "fee_structure": fee_structure_name,
                "payment_schedule": [
                    {
                        "payment_term": term['paymentTerm'],
                        "due_date": parse(term['dueDate']).strftime("%Y-%m-%d"),
                        "invoice_portion": term['invoicePortion']
                    }
                    for term in class_terms
                ]
            })
            payment_plan.save()

        return True
    except Exception as e:
        frappe.logger("walnut").exception(e)
        frappe.log_error(str(e))
        frappe.db.rollback()
        return False


def get_formatted_payment_plan(data):
    payment_plan = {}

    for payment_term in data['paymentTerms']:
        class_name = payment_term['class']
        invoice_portion = payment_term['invoicePortion']
        payment_plan[class_name] = payment_plan.get(class_name, []) + [invoice_portion]

    formatted_payment_plan = {}

    for class_name, invoice_portions in payment_plan.items():
        formatted_invoice_portions = '-'.join(map(str, invoice_portions))
        formatted_payment_plan[class_name] = formatted_invoice_portions
    return formatted_payment_plan