import frappe


def validate(doc,method=None):
    if doc.is_new():
        validate_sequence(doc)
        validate_passing_out_class_check(doc)
    else:
        old_doc = doc.get_doc_before_save()
        if old_doc.sequence != doc.sequence:
            validate_sequence(doc)
        if old_doc.custom_is_passing_out_class != doc.custom_is_passing_out_class:
            validate_passing_out_class_check(doc)
    return

def validate_sequence(doc):
    if not doc.sequence and doc.school:
        last_sequence = frappe.db.get_value('Program', {'school': doc.school}, 'sequence',order_by='sequence DESC',) or 0
        new_sequence = last_sequence + 1
        while frappe.db.exists('Program', {'school': doc.school,'sequence':new_sequence}):
            new_sequence += 1
        doc.sequence = new_sequence
    else:
        if frappe.db.exists('Program', {'school': doc.school,'sequence':doc.sequence}):
            frappe.throw("The sequence number already exists.")
    return

def validate_passing_out_class_check(doc):
    if doc.custom_is_passing_out_class:
        if frappe.db.exists('Program', {'school': doc.school,'custom_is_passing_out_class':doc.custom_is_passing_out_class}):
            frappe.throw("The passing out of class check would be limited to one class in school.")
    return