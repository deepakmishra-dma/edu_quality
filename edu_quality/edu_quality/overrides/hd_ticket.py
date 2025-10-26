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
        self.fetch_ticket_details()
        self.validate_auto_reply()

    @frappe.whitelist()
    def fetch_ticket_details(self):
        students = self.find_student_by_email() or self.find_student_by_guardian()
        if not students:
            return
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
            students = [student.parent for student in students]
            return students
    
    def get_student_details(self,student):
        if not frappe.db.exists('Student',student):
            return 
        doc = frappe.get_doc("Student",student)
        student_name = doc.first_name
        if doc.last_name:
            student_name = student_name + " " + doc.last_name
        data =  """
                <b>STUDENT DETAILS:</b> - {student_id}
                <table>
                <tr><td><b>ID</b></td><td>{student_id}</td></tr>
                <tr><td><b>Name</b></td><td> {student_name}</td></tr>
                <tr><td><b>School</b></td><td> {school}</td></tr>
                <tr><td><b>Class</b> </td><td>{program}</td></tr>
                <tr><td><b>Division</b></td><td> {division}</td></tr>
                <tr><td><b>Status</b> </td><td>{status}</td></tr>
                <tr><td><b>Contact</b> </td><td>{contact}</td></tr> 
                <tr><td><b>Bus</b> </td><td>{bus}</td></tr>
                </table>
                """.format(student_id=student,student_name=student_name,school=doc.school,program=doc.program,division=doc.custom_division,status=doc.student_status,contact=doc.student_mobile_number,bus=doc.drop_bus)
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
                            <tr>
                                <td>{payment_term}</td>         
                                <td>{due_date}</td>  
                                <td>{amount}</td>      
                                <td>{outstanding}</td>
                            </tr>
                            """
        schedule_text = """
                            <b>PAYMENT SCHEDULE:</b> - {student_id}
                            <table> 
                            <tr>
                                
                                <td><b>PAYMENT TERM</b></td> 
                                <td><b>DUE DATE</b></td>
                                <td><b>PAYMENT AMOUNT</b></td>
                                <td><b>OUTSTANDING</b></td>
                            </tr>
                            """
        for schedule in fee.payment_schedule:
            schedule_text = schedule_text.format(student_id=student.name) + payment_schedule.format(payment_term=schedule.payment_term,due_date=schedule.due_date,amount=schedule.payment_amount,outstanding=schedule.outstanding)
        schedule_text = schedule_text + """</table>"""
        url = frappe.utils.get_url_to_form("Fees",fee.name)
        fee_link = """<a href="{url}">Fee Link</a>""".format(url=url)
        data = """
                
                <b>FEE DETAILS:</b> - {student_id}
                <table>
                <tr><td><b>Payment Plan</b> </td><td>{payment_plan}</td></tr>
                <tr><td><b>Total Fee</b> </td><td>{total}</td></tr>
                <tr><td><b>Fees Paid</b> </td><td>{paid}</td></tr>
                <tr><td><b>Fee Link</b> </td><td>{fee_link}</td></tr>
                </table>
                """.format(student_id=student.name,payment_plan=payment_plan,total=fee.grand_total,paid=fee.grand_total-fee.outstanding_amount,fee_link=fee_link)
        self.description = self.description + data #+ schedule_text
        # self.get_payment_entries(fee)
    
    def get_payment_entries(self,fee):
        template = """
                    <tr>
                        <td>{payment_term}</td>
                        <td><a href="{url}">{entry}</a></td>
                    </tr>
                    """
        entries = frappe.get_all("Payment Entry",filters={'reference_name':fee.name,'docstatus':1},fields=['name','payment_term'])
        if not entries:
            return
        entry_text = """
                    <b>PAYMENT RECEIPTS:</b> - {student_id}
                    <table>
                    <tr>
                        <td><b>PAYMENT TERM</b></td>
                        <td><b>PAYMENT ENTRY</b></td>
                    </tr>
                """.format(student_id=fee.student)
        for entry in entries:
            term = entry.payment_term or "Deposit"
            url = frappe.utils.get_url_to_form("Payment Entry",entry.name)
            entry_text = entry_text + template.format(payment_term=term,entry=entry.name,url=url)
        entry_text = entry_text + "</table>"
        self.description = self.description + entry_text

    def get_pevious_tickets(self):
        tickets = frappe.db.get_all("HD Ticket",{'raised_by':self.raised_by},['name','subject'])
        if len(tickets)==1 and tickets[0].name==self.name:
            return
        elif len(tickets) == 0:
            return 
        ticket_text = """
                   
                    <b>Previous Tickets:</b>
                    <table>
                    <tr>
                        <td><b>Ticket No</b></td>
                        <td><b>Subject</b></td>
                    </tr>
                """
        template = """<tr>
                        <td><a href="{url}">{ticket_no}</a></td>
                        <td>{subject}</td>
                    </tr>
                    """
        for ticket in tickets:
            if ticket.name==self.name:
                continue
            ticket_text = ticket_text + template.format(ticket_no=ticket.name,subject=ticket.subject,url=frappe.utils.get_url_to_form("HD Ticket",ticket.name))
        if self.description:
            self.description = self.description + ticket_text + "</table>"
        else:
            self.description = ticket_text + "</table>"

    def validate_auto_reply(self):
        """
        Check if auto reply is enabled and send auto reply if enabled
        """
        mgr_settings = frappe.get_single("MGR Settings")
        if (
            mgr_settings.enable_auto_reply
            and mgr_settings.email_template
            and self.creation == self.modified
        ):
            self.auto_reply(mgr_settings.email_template)

    def auto_reply(self, template):
        """
        Send auto reply to the user
        """
        template = frappe.get_doc("Email Template", template)
        context = self.as_dict()
        subject = frappe.render_template(template.subject, context=context)
        message = frappe.render_template(template.response, context=context)
        email_account = frappe.get_doc("Email Account", {"enable_outgoing": 1})

        make_params = {
            "doctype": self.doctype,
            "name": self.name,
            "subject": subject,
            "content": message,
            "sender": email_account.email_id,
            "sender_full_name": email_account.name,
            "send_email": True,
            "recipients": self.raised_by,
            "sent_or_received": "Sent",
            "communication_type": "Communication",
            "now": True,
        }

        make(**make_params)