import frappe 
from frappe.core.doctype.communication.email import make

def student_info(students):
    students_info = []
    fees_info = []
    payment_schedule_info = []
    payment_entry_info = []

    # students = frappe.get_all('Student', filters={'user': raised_by}, fields=['name', 'first_name', 'school', 'program', 'custom_division', 'reference_number', 'student_status', 'student_mobile_number'])
    if students:
        for student in students:
            student_data = frappe.db.get_value('Student', student, ['first_name','school', 'program', 'custom_division','reference_number','student_status','student_mobile_number'])
            student_details = f"<b>Name: {student_data.first_name}</b>,<br>\nSchool: {student_data.school},<br>\nClass: {student_data.program},<br>Division: {student_data.custom_division},<br>\nReference Number: {student_data.reference_number},<br>\nStudent Status: {student_data.student_status},<br>\nPrimary Contact: {student_data.student_mobile_number} <br><br>\n\n"
            students_info.append(f"<br><b>{student_details}</b><br>")


            fees_record = frappe.get_all('Fees', filters={'student': student_data.name}, fields=['name', 'fee_schedule', 'fee_structure', 'payment_plan'])
            if fees_record:
                fees_info.append(f"<br><br>\n\nFees Information for {student_data.first_name}:\n</b>")
                for fee_data in fees_record:
                    fees_info.append(f"\n\n<br><b>Fee Schedule: {fee_data.fee_schedule}</b>,<br>\n<b>Fee Structure: {fee_data.fee_structure}</b>,<br>\n<b>Payment Plan: {fee_data.payment_plan}</b>\n<br>")
                    
                    payment_schedules = frappe.get_all('Payment Schedule', filters={'parent': fee_data['name']}, fields=['payment_term', 'description', 'due_date', 'discount', 'payment_amount', 'outstanding'])
                    formatted_payment_schedule = "\n".join([f"payment_term: {entry['payment_term']}\ndescription: {entry['description']}\ndue_date: {entry['due_date']}\ndiscount: {entry['discount']}\npayment_amount: {entry['payment_amount']}\noutstanding: {entry['outstanding']}" for entry in payment_schedules])
                    payment_schedule_info.append(f"\n<br><b>Payment Schedule for {student_data.first_name}:\n{formatted_payment_schedule}</b>\n\n<br>")

            payment_entries = frappe.get_all('Payment Entry', filters={'party': student_data['name']}, fields=['name'])
            if payment_entries:
                payment_entry_info.append(f"<br>\n\nPayment Entries for {student_data.first_name}:\n<br>")
                for entry in payment_entries:
                    payment_entry_url = frappe.utils.get_url_to_form("Payment Entry", entry.name)
                    payment_entry_info.append(f"\n<b><br>Payment Entry ID: {entry.name}</b>\n\n,<br> URL: <a><b> href={payment_entry_url}>Link</b></a><br>")

    full_text = "\n\n".join(students_info + fees_info + payment_schedule_info + payment_entry_info)
    return full_text

def get_details(raised_by):
    students = []
    if frappe.db.exists("Student",{'user': raised_by}):
        students = [frappe.db.get_value("Student", filters={'user': raised_by})]
    elif frappe.db.exists('Guardian',{'email_address': raised_by}):
        students = frappe.db.get_all("Student Guardian", filters={'guardian': frappe.db.get_value('Guardian', filters={'email_address': raised_by})}, fields=['parent'])
        students = [student['parent'] for student in students]

    return student_info(students)



def after_insert(doc, method=None):
    text = ''
    
    full_text = get_details(doc.raised_by)

    # Fetching previous tickets raised by the user
    previous_tickets_info = []
    previous_tickets = frappe.get_all('HD Ticket', filters={'raised_by': doc.raised_by}, fields=['name', 'subject', 'creation'])
    if previous_tickets:
        for ticket in previous_tickets:
            # Fetching ticket URL
            ticket_url = frappe.utils.get_url_to_form("HD Ticket", ticket['name'])
        
            # Constructing previous ticket details with URL
            previous_ticket_details = f"<br><a href={ticket_url}>Ticket ID: {ticket['name']}</a>,<br><b>Subject: {ticket['subject']}</b>,<br><b>Creation Time: {ticket['creation']}</b> <br>"
            previous_tickets_info.append(previous_ticket_details)
    
        # Update HD Ticket with previous ticket details
        frappe.db.set_value('HD Ticket', doc.name, 'custom_previous_ticket_details', "\n".join(previous_tickets_info))
        text = text + "\n\n<br>".join(previous_tickets_info)
    else:
        frappe.msgprint("No previous tickets found for the same user.")

    # Combining all information and adding it as a comment to the HD Ticket
    full_text = "\n\n".join(previous_tickets_info)
    if full_text:
        make(doctype="HD Ticket", name=doc.name, subject="Student Information", content=full_text)
    doc.reload()
