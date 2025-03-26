import frappe 
from frappe.core.doctype.communication.email import make
from frappe import _
from frappe.utils import get_user_info_for_avatar
from frappe.utils.caching import redis_cache
from pypika import Criterion, Order

from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_one as get_template
from helpdesk.utils import check_permissions, get_customer, is_agent


@frappe.whitelist()
def new(doc, attachments=[]):
    doc["doctype"] = "HD Ticket"
    doc["via_customer_portal"] = bool(frappe.session.user)
    d = frappe.get_doc(doc).insert()
    d.create_communication_via_contact(d.description, attachments)
    return d


@frappe.whitelist()
def get_one(name):
    check_permissions("HD Ticket", None)
    QBContact = frappe.qb.DocType("Contact")
    QBTicket = frappe.qb.DocType("HD Ticket")

    _is_agent = is_agent()

    query = (
        frappe.qb.from_(QBTicket)
        .select(QBTicket.star)
        .where(QBTicket.name == name)
        .limit(1)
    )

    if not _is_agent:
        query = query.where(get_customer_criteria())

    ticket = query.run(as_dict=True)
    if not len(ticket):
        frappe.throw(_("Ticket not found"), frappe.DoesNotExistError)
    ticket = ticket.pop()

    contact = (
        frappe.qb.from_(QBContact)
        .select(
            QBContact.company_name,
            QBContact.email_id,
            QBContact.image,
            QBContact.mobile_no,
            QBContact.name,
            QBContact.phone,
        )
        .where(QBContact.name == ticket.contact)
        .run(as_dict=True)
    )
    if contact:
        contact = contact[0]

    return {
        **ticket,
        "assignee": get_assignee(ticket._assign),
        "comments": get_comments(name),
        "communications": get_communications(name),
        "contact": contact,
        "history": get_history(name),
        "tags": get_tags(name),
        "template": get_template(ticket.template or DEFAULT_TICKET_TEMPLATE),
        "views": get_views(name),
    }


def get_customer_criteria():
    QBTicket = frappe.qb.DocType("HD Ticket")
    user = frappe.session.user
    conditions = [
        QBTicket.contact == user,
        QBTicket.raised_by == user,
    ]
    customer = get_customer(user)
    for c in customer:
        conditions.append(QBTicket.customer == c)
    return Criterion.any(conditions)


def get_assignee(_assign: str):
    j = frappe.parse_json(_assign)
    if not j or len(j) < 1:
        return
    return get_user_info_for_avatar(j.pop())


def get_communications(ticket: str):
    QBCommunication = frappe.qb.DocType("Communication")
    communications = (
        frappe.qb.from_(QBCommunication)
        .select(
            QBCommunication.bcc,
            QBCommunication.cc,
            QBCommunication.content,
            QBCommunication.creation,
            QBCommunication.name,
            QBCommunication.sender,
            QBCommunication.recipients,
        )
        .where(QBCommunication.reference_doctype == "HD Ticket")
        .where(QBCommunication.reference_name == ticket)
        .orderby(QBCommunication.creation, order=Order.asc)
        .run(as_dict=True)
    )
    roles = frappe.get_roles()
    if "Guardian" in roles:
        communications = [c for c in communications if frappe.session.user in c.recipients]
    for c in communications:
        c.attachments = get_attachments("Communication", c.name)
        c.user = get_user_info_for_avatar(c.sender)
    return communications


def get_comments(ticket: str):
    if not frappe.has_permission("HD Ticket Comment", "read"):
        return []
    QBComment = frappe.qb.DocType("HD Ticket Comment")
    comments = (
        frappe.qb.from_(QBComment)
        .select(
            QBComment.commented_by,
            QBComment.content,
            QBComment.creation,
            QBComment.is_pinned,
            QBComment.name,
        )
        .where(QBComment.reference_ticket == ticket)
        .orderby(QBComment.creation, order=Order.asc)
        .run(as_dict=True)
    )
    for c in comments:
        c.user = get_user_info_for_avatar(c.commented_by)
    return comments


def get_history(ticket: str):
    if not frappe.has_permission("HD Ticket Activity", "read"):
        return []
    QBActivity = frappe.qb.DocType("HD Ticket Activity")
    history = (
        frappe.qb.from_(QBActivity)
        .select(
            QBActivity.name, QBActivity.action, QBActivity.owner, QBActivity.creation
        )
        .where(QBActivity.ticket == ticket)
        .orderby(QBActivity.creation, order=Order.desc)
    )
    history = history.run(as_dict=True)
    for h in history:
        h.user = get_user_info_for_avatar(h.owner)
    return history


def get_views(ticket: str):
    QBViewLog = frappe.qb.DocType("View Log")
    views = (
        frappe.qb.from_(QBViewLog)
        .select(
            QBViewLog.creation,
            QBViewLog.name,
            QBViewLog.viewed_by,
        )
        .where(QBViewLog.reference_doctype == "HD Ticket")
        .where(QBViewLog.reference_name == ticket)
        .orderby(QBViewLog.creation, order=Order.desc)
        .run(as_dict=True)
    )
    for v in views:
        v.user = get_user_info_for_avatar(v.viewed_by)
    return views


def get_tags(ticket: str):
    QBTag = frappe.qb.DocType("Tag Link")
    rows = (
        frappe.qb.from_(QBTag)
        .select(QBTag.tag)
        .where(QBTag.document_type == "HD Ticket")
        .where(QBTag.document_name == ticket)
        .orderby(QBTag.creation, order=Order.asc)
        .run(as_dict=True)
    )
    res = []
    for tag in rows:
        res.append(tag.tag)
    return res


@redis_cache()
def get_attachments(doctype, name):
    QBFile = frappe.qb.DocType("File")

    return (
        frappe.qb.from_(QBFile)
        .select(QBFile.name, QBFile.file_url, QBFile.file_name)
        .where(QBFile.attached_to_doctype == doctype)
        .where(QBFile.attached_to_name == name)
        .run(as_dict=True)
    )



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
    if full_text:
        make(doctype="HD Ticket", name=doc.name, subject="Student Information", content=full_text,communication_type="Communication")
    doc.reload()

