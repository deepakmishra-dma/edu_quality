import frappe 
from frappe.core.doctype.communication.email import make

def get_student_info(raised_by):
    students_info = []
    fees_info = []
    payment_schedule_info = []
    payment_entry_info = []

    students = frappe.get_all('Student', filters={'user': raised_by}, fields=['name', 'first_name', 'school', 'program', 'custom_division', 'reference_number', 'student_status', 'student_mobile_number'])
    if students:
        for student_data in students:
            student_details = f"<b>Name: {student_data.get('first_name')}</b>,\nSchool: {student_data.get('school')},\nClass: {student_data.get('program')},Division: {student_data.get('custom_division')},\nReference Number: {student_data.get('reference_number')},\nStudent Status: {student_data.get('student_status')},\nPrimary Contact: {student_data.get('student_mobile_number')} \n\n"
            students_info.append(f"{student_details}<br>")

            student_reference_number = student_data.get('reference_number')
            fees_record = frappe.get_all('Fees', filters={'student_reference_number': student_reference_number}, fields=['name', 'fee_schedule', 'fee_structure', 'payment_plan'])
            if fees_record:
                fees_info.append(f"\n\nFees Information for {student_data.get('first_name')}:\n")
                for fee_data in fees_record:
                    fees_info.append(f"\n\n<b>Fee Schedule: {fee_data.get('fee_schedule')}</b>,<br>\n<b>Fee Structure: {fee_data.get('fee_structure')}</b>,<br>\n<b>Payment Plan: {fee_data.get('payment_plan')}</b>\n<br>")
                    
                    payment_schedules = frappe.get_all('Payment Schedule', filters={'parent': fee_data['name']}, fields=['payment_term', 'description', 'due_date', 'discount', 'payment_amount', 'outstanding'])
                    formatted_payment_schedule = "\n".join([f"payment_term: {entry['payment_term']}\ndescription: {entry['description']}\ndue_date: {entry['due_date']}\ndiscount: {entry['discount']}\npayment_amount: {entry['payment_amount']}\noutstanding: {entry['outstanding']}" for entry in payment_schedules])
                    payment_schedule_info.append(f"\n<b>Payment Schedule for {student_data.get('first_name')}:\n{formatted_payment_schedule}</b>\n\n<br>")

            payment_entries = frappe.get_all('Payment Entry', filters={'party': student_data['name']}, fields=['name'])
            if payment_entries:
                payment_entry_info.append(f"\n\nPayment Entries for {student_data.get('first_name')}:\n")
                for entry in payment_entries:
                    payment_entry_url = frappe.utils.get_url_to_form("Payment Entry", entry.get('name'))
                    payment_entry_info.append(f"\n<b>Payment Entry ID: {entry.get('name')}</b>\n\n, URL: <a><b> href={payment_entry_url}>Link</b></a><br>")

    return students_info, fees_info, payment_schedule_info, payment_entry_info


def get_guardian_info(raised_by):
    students_info = []
    guardians = frappe.get_all('Guardian', filters={'email_address': raised_by}, fields=['name', 'first_name', 'last_name', 'mobile_number'])
    if guardians:
        for guardian_data in guardians:
            guardian_name = guardian_data.get('name')
            matching_students = []
            student_guardians = frappe.get_all('Student Guardian', filters={'guardian': guardian_name}, fields=['parent'])
            if student_guardians:
                matching_students = frappe.get_all('Student', filters={'name': ('in', [sg['parent'] for sg in student_guardians])}, fields=['name', 'first_name','school', 'program', 'custom_division', 'reference_number', 'student_status', 'student_mobile_number'])
        
            if matching_students:
                for student_data in matching_students:
                    student_details = f"\n\nName: {student_data.get('first_name')},\nSchool: {student_data.get('school')},\nClass: {student_data.get('program')},\nDivision: {student_data.get('custom_division')},\nReference Number: {student_data.get('reference_number')},\nStudent Status: {student_data.get('student_status')},\nPrimary Contact: {student_data.get('student_mobile_number')} \n\n"
                    students_info.append(student_details)

    return students_info


def after_insert(doc, method=None):
    text = ''
    raised_by = doc.raised_by

    # Get student information
    students_info, fees_info, payment_schedule_info, payment_entry_info = get_student_info(raised_by)

    # Get guardian information
    students_info += get_guardian_info(raised_by)

    # Fetching previous tickets raised by the user
    previous_tickets_info = []
    previous_tickets = frappe.get_all('HD Ticket', filters={'raised_by': raised_by}, fields=['name', 'subject', 'creation'])
    if previous_tickets:
        for ticket in previous_tickets:
            # Fetching ticket URL
            ticket_url = frappe.utils.get_url_to_form("HD Ticket", ticket['name'])
        
            # Constructing previous ticket details with URL
            previous_ticket_details = f"\n\n<a href={ticket_url}>Ticket ID: {ticket['name']}</a><br>, \n\n <b>Subject: {ticket['subject']}</b></n><br>, \n\n<b>Creation Time: {ticket['creation']}</b> <br>\n\n"
            previous_tickets_info.append(previous_ticket_details)
    
        # Update HD Ticket with previous ticket details
        frappe.db.set_value('HD Ticket', doc.name, 'custom_previous_ticket_details', "\n".join(previous_tickets_info))
        text = text + "\n\n".join(previous_tickets_info)
    else:
        frappe.msgprint("No previous tickets found for the same user.")

    # Combining all information and adding it as a comment to the HD Ticket
    full_text = "\n\n".join(students_info + fees_info + payment_schedule_info + payment_entry_info + previous_tickets_info)
    if full_text:
        make(doctype="HD Ticket", name=doc.name, subject="Student Information", content=full_text)
    doc.reload()
