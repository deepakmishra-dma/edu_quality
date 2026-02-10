
__version__ = '0.0.1'

# Override the has_permission method of the Event class using monkey patching
from frappe.desk.doctype.event import event
event.has_permission = lambda ptype, user=None: True
event.get_permission_query_conditions = lambda user: []