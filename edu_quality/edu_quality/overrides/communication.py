import frappe
from frappe.core.doctype.communication.communication import Communication


class CustomCommunication(Communication):
	def before_insert(self):
		self.validate_hd_ticket()

	def validate_hd_ticket(self):
		"""
		Check if the reference is a HD Ticket and if it is closed, create a new ticket
		"""
		if self.reference_doctype == "HD Ticket":
			status = frappe.db.get_value("HD Ticket", self.reference_name, "status")
			if status == "Closed":
				self.create_hd_ticket()

	def create_hd_ticket(self):
		"""
		Create a new HD Ticket from the communication
		"""
		hd_ticket = frappe.new_doc("HD Ticket")
		hd_ticket.previous_ticket = self.reference_name
		hd_ticket.raised_by = self.sender
		hd_ticket.subject = self.subject
		hd_ticket.insert(ignore_permissions=True)
		# change the reference of the communication to the new ticket
		self.reference_name = hd_ticket.name
