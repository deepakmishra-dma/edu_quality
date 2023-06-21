import frappe


def before_save(doc,method=None):
    if doc.student_admission:
        doc.application_fees = frappe.get_value("Student Admission Program",{'parent':doc.student_admission,'program':doc.program},'application_fee')
    fee_schedule_filter = {
        'program':doc.program,
        'academic_year':doc.academic_year,
        'docstatus': 1
    }
    if doc.academic_term:
        fee_schedule_filter['academic_term'] = doc.academic_term
    fee_schedule = frappe.get_doc('Fee Schedule',fee_schedule_filter)
    doc.fee_schedule = fee_schedule.name 
    doc.fee_structure = fee_schedule.fee_structure
    doc.fee_components = []
    for component in fee_schedule.components:
        doc.append('fee_components',{
            'fees_category':component.fees_category,
            'amount':component.amount,
            'description': component.description
            })
    get_deposits(doc)
    calculate_total(doc)

def calculate_total(doc):
    doc.total_amount = 0
    if doc.application_fees:
        doc.total_amount+= doc.application_fees
    for component in doc.fee_components:
        doc.total_amount += component.amount
    for deposit in doc.deposits:
        doc.total_amount += deposit.amount

def get_deposits(doc):
    doc.deposits = []
    deposits = frappe.get_list('Security Deposit',{'program':doc.program,'academic_year':doc.academic_year},['name','amount'])
    for deposit in deposits:
        doc.append('deposits',{
            'safety_deposit': deposit.name,
            'amount': deposit.amount
        })
    
