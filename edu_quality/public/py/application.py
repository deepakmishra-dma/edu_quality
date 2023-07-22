import frappe


def before_save(doc,method=None):
    if doc.student_admission:
        doc.application_fees = frappe.get_value("Student Admission Program",{'parent':doc.student_admission,'program':doc.program},'application_fee')
    if doc.fee_structure:
        fee_structure = frappe.get_doc("Fee Structure", doc.fee_structure)
        doc.fee_components = []
        if frappe.db.get_single_value("Fees Settings",'apply_fees'):
            for component in fee_structure.components:
                doc.append('fee_components',{
                    'fees_category':component.fees_category,
                    'amount':component.amount,
                    'description': component.description
                    })
    else:
        frappe.throw("Fee Structure is Mandatory")
    if frappe.db.get_single_value("Fees Settings",'apply_deposits'):
        get_deposits(doc)
    calculate_total(doc)

def calculate_total(doc):
    doc.total_amount = 0
    if doc.application_fees:
        doc.total_amount+= float(doc.application_fees)
    for component in doc.fee_components:
        doc.total_amount += float(component.amount)

def get_deposits(doc):
    deposits = frappe.get_list('Security Deposit',{'program':doc.program,'academic_year':doc.academic_year},['name','amount'])
    for deposit in deposits:
        doc.append('fee_components',{
            'fees_category': deposit.name,
            'amount': deposit.amount
        })
    
