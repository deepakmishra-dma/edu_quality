import frappe.utils
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket
import frappe
from frappe.core.doctype.communication.email import make
from datetime import datetime
class CustomHDTicket(HDTicket):
    def on_communication_update(self, c):
        # If communication is incoming, then it is a reply from customer, and ticket must
        # be reopened.
        if c.sent_or_received == "Received":
            self.status = "Open"
        # If communication is outgoing, it must be a reply from agent
        if c.sent_or_received == "Sent":
            # Set first response date if not set already
            self.first_responded_on = (
                self.first_responded_on or frappe.utils.now_datetime()
            )
        # Fetch description from communication if not set already. This might not be needed
        # anymore as a communication is created when a ticket is created.
        self.description = self.description or c.content
        # Save the ticket, allowing for hooks to run.
        self.save(ignore_permissions=True)

    def after_insert(self):
        students = self.find_student_by_email() or self.find_student_by_guardian()
        for student in students:
            self.get_student_details(student)
        self.get_pevious_tickets()
        make(doctype="HD Ticket", name=self.name, subject="Student Information", content=self.description,communication_type="Communication")

    def find_student_by_email(self):
        if frappe.db.exists("Student",{'user':self.raised_by}):
            return [frappe.get_value("Student",{'user':self.raised_by})]
        else:
            return None
    
    def find_student_by_guardian(self):
        if frappe.db.exists('Guardian',{'email_address':self.raised_by}):
            guardian = frappe.get_value("Guardian",{'email_address':self.raised_by})
            students = frappe.get_all('Student Guardian',filters={'guardian':guardian},fields=['parent'])
            return students
    
    def get_student_details(self,student):
        if not frappe.db.exists('Student',student):
            return 
        doc = frappe.get_doc("Student",student)
        student_name = doc.first_name
        if doc.last_name:
            student_name = student_name + " " + doc.last_name
        data =  """
                <br><br>
                -------------------------------------------<br>
                <b>STUDENT DETAILS</b> - {student_id}<br>
                -------------------------------------------<br>
                <b>ID:</b> {student_id}<br>
                <b>Name:</b> {student_name}<br>
                <b>School:</b> {school}<br>
                <b>Class:</b> {program}<br>
                <b>Division:</b> {division}<br>
                <b>Status:</b> {status}<br>
                <b>Contact:</b> {contact}<br> 
                --------------------------------------------<br>
                """.format(student_id=student,student_name=student_name,school=doc.school,program=doc.program,division=doc.custom_division,status=doc.student_status,contact=doc.student_mobile_number)
        self.description = data
        self.get_fee_details(doc)
    
    def get_fee_details(self,student):
        ac_yr = frappe.db.get_value("Academic Year",{'custom_current_academic_year':1})
        if not frappe.db.exists('Fees',{'student':student.name,'academic_year':ac_yr}):
            return
        fee = frappe.get_doc("Fees",{'student':student.name,'academic_year':ac_yr})
        payment_plan = fee.payment_plan[0:2]
        next_due = "Nil"
        overdue = "Nil"
        payment_schedule = """
                            <br><br>
                            -------------------------------------------<br>
                            <b>PAYMENT SCHEDULE</b><br>
                            -------------------------------------------<br>
                            <b>Payment Term:</b> {payment_term}<br>
                            <b>Due Date:</b> {due_date}<br>
                            <b>Discount:</b> {discount}<br>
                            <b>Payment Amount:</b> {amount}<br>
                            <b>Outstanding:</b> {outstanding}<br>
                            --------------------------------------------<br>
                            """
        schedule_text = ""
        for schedule in fee.payment_schedule:
            if schedule.outstanding>0:
                next_due = schedule.payment_term +" - " + str(schedule.outstanding) + " Due On -" + str(schedule.due_date)
            if schedule.due_date<datetime.now().date():
                overdue = next_due
            schedule_text = schedule_text + payment_schedule.format(payment_term=schedule.payment_term,due_date=schedule.due_date,discount=schedule.discount_breakup,amount=schedule.payment_amount,outstanding=schedule.outstanding)
        url = frappe.utils.get_url_to_form("Fees",fee.name)
        fee_link = """<a href="{url}">Fee Link</a>""".format(url=url)
        data = """
                <br><br>
                -------------------------------------------<br>
                <b>FEE DETAILS</b> - {student_id} <br>
                -------------------------------------------<br>
                <b>Payment Plan:</b> {payment_plan}<br>
                <b>Total Fee:</b> {total}<br>
                <b>Fees Paid:</b> {paid}<br>
                <b>Next Due:</b> {next_due}<br>
                <b>Overdue:</b> {overdue}<br>
                <b>Fee Link:</b> {fee_link}<br>
                --------------------------------------------<br>
                """.format(student_id=student.name,payment_plan=payment_plan,total=fee.grand_total,paid=fee.grand_total-fee.outstanding_amount,next_due=next_due,overdue=overdue,fee_link=fee_link)
        self.description = self.description + data + schedule_text
        self.get_payment_entries(fee)
    
    def get_payment_entries(self,fee):
        template = """Payment Entry: {payment_term} - <a href="{url}">{entry}</a><br>"""
        entries = frappe.get_all("Payment Entry",filters={'reference_no':fee.name,'docstatus':1},fields=['name','payment_term'])
        if not entries:
            return
        entry_text = """
                    <br><br>
                    ----------------------------------------<br>
                    PAYMENT RECEIPTS - {student_id}<br>
                    ----------------------------------------<br>
                """.format(student_id=fee.student)
        for entry in entries:
            term = entry.payment_term or "Deposit"
            url = frappe.utils.get_url_to_form("Payment Entry",entry.name)
            entry_text = entry_text + template.format(payment_term=term,entry=entry.name,url=url)
        entry_text = entry_text + "----------------------------------------<br>"
        self.description = self.description + entry_text

    def get_pevious_tickets(self):
        tickets = frappe.db.get_all("HD Ticket",{'raised_by':self.raised_by},['name','subject'])
        if len(tickets)==1 and tickets[0].name==self.name:
            return
        elif len(tickets) == 0:
            return 
        ticket_text = """
                    <br><br>
                    ----------------------------------------<br>
                    <b>Previous Tickets</b><br>
                    ----------------------------------------<br>
                """
        template = """<b>Support Ticket:</b> {subject} - <a href="{url}">{ticket}</a><br>"""
        for ticket in tickets:
            if ticket.name==self.name:
                continue
            ticket_text = ticket_text + template.format(subject=ticket.subject,ticket=ticket.name,url=frappe.utils.get_url_to_form("HD Ticket",ticket.name))
        if self.description:
            self.description = self.description + ticket_text + "----------------------------------------<br>"
        else:
            self.description = ticket_text + "----------------------------------------<br>"

