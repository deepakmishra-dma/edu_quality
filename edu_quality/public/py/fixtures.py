import frappe


def custom_fields(doc,method=None):
    doc.module = "Edu Quality"
    doc.save()

def custom_doc_perm(doc,method=None):
    doc.custom_module = "Edu Quality"
    doc.save()