import frappe 
from frappe.core.doctype.communication.email import make

def after_insert(doc,method=None):
    text = ''
    students_info = []
    fees_info = []
    payment_schedule_info = []
    payment_entry_info = []
    previous_tickets_info = []
    
    students = frappe.get_all('Student', filters={'user': doc.raised_by}, fields=['name', 'first_name', 'school', 'program', 'custom_division', 'reference_number', 'student_status', 'student_mobile_number'])
    if students:
        for student_data in students:
            student_details = f"<br><br><b>Name: {student_data.get('first_name')}</b>,<br>\nSchool: {student_data.get('school')},<br>\n Class: {student_data.get('program')},<br>\nDivision: {student_data.get('custom_division')},\n<br>Reference Number: {student_data.get('reference_number')},<br>\nStudent Status: {student_data.get('student_status')},<br>\nPrimary Contact: {student_data.get('student_mobile_number')} <br><br>\n\n"
            students_info.append(f"<br>student_details")
            student_reference_number = student_data.get('reference_number')
            
            fees_record = frappe.get_all('Fees', filters={'student_reference_number': student_reference_number}, fields=['name', 'fee_schedule', 'fee_structure', 'payment_plan'])
            if fees_record:
                fees_info.append(f"<br><br>\n\n<b>Fees Information for {student_data.get('first_name')}:</b>\n")
                for fee_data in fees_record:
                    fees_info.append(f"\n\n<br><br>Fee Schedule: {fee_data.get('fee_schedule')},<br>\nFee Structure: {fee_data.get('fee_structure')},\n<br>Payment Plan: {fee_data.get('payment_plan')}<br><br>")
                
                    payment_schedules = frappe.get_all('Payment Schedule', filters={'parent': fee_data['name']}, fields=['payment_term', 'description', 'due_date', 'discount', 'payment_amount', 'outstanding'])
                    formatted_payment_schedule = "\n".join([f"<br><br><b>Payment_term: {entry['payment_term']}\n</b><br>Description: {entry['description']}\n<br>Due Date: {entry['due_date']}\n<br>Discount: {entry['discount']}\n<br>Payment Amount: {entry['payment_amount']}\n<br>Outstanding: {entry['outstanding']}<br><br>\n\n" for entry in payment_schedules])
                    payment_schedule_info.append(f"\n<br><b>Payment Schedule for {student_data.get('first_name')}:</b>\n{formatted_payment_schedule}")

            # Fetching Payment Entry records for the current student
            payment_entries = frappe.get_all('Payment Entry', filters={'party': student_data['name']}, fields=['name'])
            if payment_entries:
                payment_entry_info.append(f"\n\n<br><b>Payment Entries for {student_data.get('first_name')}:</b><br>\n")
                for entry in payment_entries:
                    payment_entry_url = frappe.utils.get_url_to_form("Payment Entry", entry.get('name'))
                    payment_entry_info.append(f"\n<br><br><b>Payment Entry ID:{entry.get('name')}<b>, URL:<a href={payment_entry_url}</a><br><br>")

    guardians = frappe.get_all('Guardian', filters={'email_address': doc.raised_by}, fields=['name', 'first_name', 'last_name', 'mobile_number'])
    if guardians:
        for guardian_data in guardians:
            guardian_name = guardian_data.get('name')  # Fetching the document name of the guardian
            matching_students = []
            student_guardians = frappe.get_all('Student Guardian', filters={'guardian': guardian_name}, fields=['parent'])
            if student_guardians:
                matching_students = frappe.get_all('Student', filters={'name': ('in', [sg['parent'] for sg in student_guardians])}, fields=['name', 'first_name','school', 'program', 'custom_division', 'reference_number', 'student_status', 'student_mobile_number'])
        
            if matching_students:
                for student_data in matching_students:
                    student_details = f"<br><br><b>Name: {student_data.get('first_name')}</b>,\n<br>School: {student_data.get('school')},\n<br>Class: {student_data.get('program')},<br>Division: {student_data.get('custom_division')},\n<br>Reference Number: {student_data.get('reference_number')},\n<br>Student Status: {student_data.get('student_status')},\n<br>Primary Contact: {student_data.get('student_mobile_number')} \n\n"
                    students_info.append(student_details)
                
                    student_reference_number = student_data.get('reference_number')
                    fees_record = frappe.get_all('Fees', filters={'student_reference_number': student_reference_number}, fields=['name', 'fee_schedule', 'fee_structure', 'payment_plan'])
                
                    if fees_record:
                        fees_info.append(f"\n<br><br><b>Fees Information for {student_data.get('first_name')}:</b>\n")
                    
                        for fee_data in fees_record:
                            fees_info.append(f"\n\n<br><br>Fee Schedule: {fee_data.get('fee_schedule')},<br>\nFee Structure: {fee_data.get('fee_structure')},<br>\nPayment Plan: {fee_data.get('payment_plan')}<br>\n")
                        
                            payment_schedules = frappe.get_all('Payment Schedule', filters={'parent': fee_data['name']}, fields=['payment_term', 'description', 'due_date', 'discount', 'payment_amount', 'outstanding'])
                            formatted_payment_schedule = "\n".join([f"<br><br><b>Payment_term: {entry['payment_term']}\n<br>Description: {entry['description']}\n<br>Due_date: {entry['due_date']}\n<br>Discount: {entry['discount']}\n<br>Payment_amount: {entry['payment_amount']}\n<br>Outstanding: {entry['outstanding']}<br>\n" for entry in payment_schedules])
                            payment_schedule_info.append(f"\n<br><b>Payment Schedule for {student_data.get('first_name')}:</b>\n{formatted_payment_schedule}")

                    # Fetching Payment Entry records for the current student
                    payment_entries = frappe.get_all('Payment Entry', filters={'party': student_data['name']}, fields=['name'])
                    if payment_entries:
                        payment_entry_info.append(f"\n\n<br><br><b>Payment Entries for {student_data.get('first_name')}:</b>\n")
                        for entry in payment_entries:
                            payment_entry_url = frappe.utils.get_url_to_form("Payment Entry", entry.get('name'))
                            payment_entry_info.append(f"\n<br><br><b>Payment Entry ID:{entry.get('name')}<b>, URL:<a href={payment_entry_url}</a><br><br>")

    # Fetching previous tickets raised by the user
    previous_tickets = frappe.get_all('HD Ticket', filters={'raised_by': doc.raised_by}, fields=['name', 'subject'])
    if previous_tickets:
        for ticket in previous_tickets:
            # Fetching ticket URL
            ticket_url = frappe.utils.get_url_to_form("HD Ticket", ticket['name'])
        
            # Constructing previous ticket details with URL
            previous_ticket_details = f"<br><b><a href={ticket_url}>Ticket ID: {ticket['name']}</a></b>, Subject: {ticket['subject']}, URL: {ticket_url}"
            #
            previous_tickets_info.append(previous_ticket_details)
    
        # Update HD Ticket with previous ticket details
        frappe.db.set_value('HD Ticket', doc.name, 'custom_previous_ticket_details', "\n".join(previous_tickets_info))
        text = text + "\n\n".join(f"<br>\nprevious_tickets_info")
    else:
        frappe.msgprint("No previous tickets found for the same user.")

    # Combining all information and adding it as a comment to the HD Ticket
    full_text = "\n\n".join(students_info + fees_info + payment_schedule_info + payment_entry_info + previous_tickets_info)
    make(doctype="HD Ticket", name=doc.name, subject="Student Information", content=full_text)
    doc.reload()

