import frappe


def validate(doc,method=None):
    if doc.is_new():
        doc.sequence = None
    if not doc.sequence and doc.school:
        last_sequence = frappe.db.get_value('Program', {'school': doc.school}, 'sequence',order_by='sequence DESC',) or 0
        doc.sequence = last_sequence + 1