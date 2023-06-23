import frappe 

def create_fees(doc,method=None):
    try:
        doc = frappe.get_doc("Student",doc.student)
        if doc.student_applicant:
            student_applicant = frappe.get_doc("Student Applicant",doc.student_applicant)
            fees = frappe.get_doc({
                "doctype": "Fees",
                "student": doc.name,
                "program_enrollment": frappe.db.get_value("Program Enrollment",{'student': doc.name},'name'),
                "fee_structure": student_applicant.fee_structure,
                "fee_schedule": student_applicant.fee_schedule,
                "company": student_applicant.institution,
                "due_date": frappe.db.get_value("Fee Schedule",student_applicant.fee_schedule,'due_date')
            })
            if student_applicant.application_fees:
                fees.append("components",{
                    'fees_category':"Application Fees",
                    'amount':student_applicant.application_fees
                })
            for component in student_applicant.fee_components:
                total += component.amount
                fees.append("components",{
                    'fees_category':component.fees_category,
                    'amount':component.amount,
                    'description': component.description
                })
            for deposit in student_applicant.deposits:
                fees.append("components",{
                    'fees_category': deposit.safety_deposit,
                    'amount': deposit.amount
                })
            fees.insert()
            fees.submit()
    except Exception as e:
        frappe.throw(str(e))


def fees_after_insert(doc,method=None):
    for fee in doc.components:
        if frappe.db.exists("Security Deposit",fee.fees_category):
            log = frappe.new_doc("Security Deposit Entry")
            log.security_deposit = fee.fees_category 
            log.amount_paid = fee.amount 
            log.fees = doc.name 
            log.insert()