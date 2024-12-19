import frappe 

from erpnext.accounts.general_ledger import make_reverse_gl_entries


def execute():
    gl_entry = frappe.qb.DocType("GL Entry")
    sales_entries = []
    account_list = [{"account":"Fee Advance - UESF","against":"Sales - UESF"}, {"account":"Fee Advance - RESPL","against":"Sales - RESPL"}]
    for entry in account_list:
        gl_entries = (
            frappe.qb.from_(gl_entry)
            .select("*")
            .where(gl_entry.account == entry['account'])
            .where(gl_entry.against == entry['against'])
            .where(gl_entry.is_cancelled == 0)
            .for_update()
        ).run(as_dict=1)
        for entry in gl_entries:
            sale_entry = (
            frappe.qb.from_(gl_entry)
            .select("*")
            .where(gl_entry.account == entry['against'])
            .where(gl_entry.credit == entry['debit'])
            .where(gl_entry.is_cancelled == 0)
            .for_update()
            ).run(as_dict=1)
            for entry in sale_entry:
                sales_entries.append(entry)
            frappe.logger("s_entry").exception(sales_entries)
        make_reverse_gl_entries(gl_entries=sales_entries)
