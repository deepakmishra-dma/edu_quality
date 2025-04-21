from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket


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