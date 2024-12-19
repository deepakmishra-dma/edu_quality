import frappe 

from erpnext.accounts.general_ledger import make_reverse_gl_entries


def execute():
    gl_entry = frappe.qb.DocType("GL Entry")
    gl_entries = (
        frappe.qb.from_(gl_entry)
        .select("*")
        .where(gl_entry.voucher_type == "Fee Advance - UESF")
        .where(gl_entry.against == "Sales - UESF")
        .where(gl_entry.is_cancelled == 0)
        .for_update()
    ).run(as_dict=1)
    frappe.logger('entry').exception(gl_entries)
    make_reverse_gl_entries(gl_entries=gl_entries)
    gl_entries = (
        frappe.qb.from_(gl_entry)
        .select("*")
        .where(gl_entry.voucher_type == "Fee Advance - RESPL")
        .where(gl_entry.against == "Sales - RESPL")
        .where(gl_entry.is_cancelled == 0)
        .for_update()
    ).run(as_dict=1)
    frappe.logger('entry').exception(gl_entries)
    make_reverse_gl_entries(gl_entries=gl_entries)
