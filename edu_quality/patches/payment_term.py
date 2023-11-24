import frappe 

data = [
    {
        "name": "Term 1",
        "payment_term_name": "Term 1",
        "invoice_portion": 0,
        "due_date_based_on": "Day(s) after invoice date",
        "credit_days": 0,
        "credit_months": 0,
        "discount_type": "Percentage",
        "discount": 0,
        "discount_validity_based_on": "Day(s) after invoice date",
        "discount_validity": 0,
        "doctype": "Payment Term"
    },
    {
        "name": "Term 2",
        "payment_term_name": "Term 2",
        "invoice_portion": 0,
        "due_date_based_on": "Day(s) after invoice date",
        "credit_days": 0,
        "credit_months": 0,
        "discount_type": "Percentage",
        "discount": 0,
        "discount_validity_based_on": "Day(s) after invoice date",
        "discount_validity": 0,
        "doctype": "Payment Term"
    },
    {
        "name": "Term 3",
        "payment_term_name": "Term 3",
        "invoice_portion": 0,
        "due_date_based_on": "Day(s) after invoice date",
        "credit_days": 0,
        "credit_months": 0,
        "discount_type": "Percentage",
        "discount": 0,
        "discount_validity_based_on": "Day(s) after invoice date",
        "discount_validity": 0,
        "doctype": "Payment Term"
    },
    {
        "name": "Term 4",
        "payment_term_name": "Term 4",
        "invoice_portion": 0,
        "due_date_based_on": "Day(s) after invoice date",
        "credit_days": 0,
        "credit_months": 0,
        "discount_type": "Percentage",
        "discount": 0,
        "discount_validity_based_on": "Day(s) after invoice date",
        "discount_validity": 0,
        "doctype": "Payment Term"
    },
    {
        "name": "Deposit",
        "payment_term_name": "Deposit",
        "invoice_portion": 0,
        "due_date_based_on": "Day(s) after invoice date",
        "credit_days": 0,
        "credit_months": 0,
        "discount_type": "Percentage",
        "discount": 0,
        "discount_validity_based_on": "Day(s) after invoice date",
        "discount_validity": 0,
        "doctype": "Payment Term"
    }
]

def execute():
    for template in data:
        if not frappe.db.exists("Payment Term",{'name': template.get('name')}):
            doc = frappe.get_doc(template)
            doc.insert()