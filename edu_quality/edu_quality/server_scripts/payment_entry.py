import frappe


def validate(doc, method=None):
    doc.letter_head = None