import frappe
import json
from dateutil.parser import parse



@frappe.whitelist()
def create_payment_plans(**kwargs):
    try:
        # Parse the submission data
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
        # Create Payment Plan documents
        for class_name, class_terms in class_payment_terms.items():
            if not frappe.db.exists("Fee Structure",{"academic_year":academic_year,"school":school,"program":term["class"]},"name"):
                frappe.throw("Fee Structure not found for this class "+str(term["class"]))
                return False
            if frappe.db.exists("Payment Plan",{"academic_year":academic_year,"school":school,"program":term["class"]},"name"):
                frappe.throw("Payment Plan already exists for this class "+str(term["class"]))
                return False
            payment_plan = frappe.get_doc({
                "doctype": "Payment Plan",
                "plan_name": plan_name,
                "academic_year": academic_year,
                "school": school,
                "program": class_name,
                "fee_structure" : frappe.get_value("Fee Structure",{"academic_year":academic_year,"school":school,"program":term["class"]},"name"),
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