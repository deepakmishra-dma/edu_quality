import frappe 
from frappe import _
from frappe.model.naming import make_autoname
from erpnext.accounts.utils import cancel_exchange_gain_loss_journal
from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry


class customJournalEntry(JournalEntry):

    def autoname(self):
        if self.is_petty_cash:
            name = self.generate_petty_cash_name()
            if name:
                self.name = name
                return

    def generate_petty_cash_name(self):
        user_remark = frappe.json.loads(self.user_remark)
        school = user_remark.get("School")
        if school:
            prefix = frappe.get_value("School", school, "prefix")
            if prefix:
                series = "PCJV-" + prefix + "-.#####"
                return make_autoname(series)
        return None


    def validate_party(self):
        for d in self.get("accounts"):
            account_type = frappe.get_cached_value("Account", d.account, "account_type")
            if account_type in ["Receivable", "Payable"]:
                if d.party_type == 'Student':
                    return
                if not (d.party_type and d.party):
                    frappe.throw(
                        _(
                            "Row {0}: Party Type and Party is required for Receivable / Payable account {1}"
                        ).format(d.idx, d.account)
                    )
                elif (
                    d.party_type
                    and frappe.db.get_value("Party Type", d.party_type, "account_type") != account_type
                ):
                    frappe.throw(
                        _("Row {0}: Account {1} and Party Type {2} have different account types").format(
                            d.idx, d.account, d.party_type
                        )
                    ) 
    
    def make_gl_entries(self, cancel=0, adv_adj=0):
        from erpnext.accounts.general_ledger import make_gl_entries

        merge_entries = frappe.db.get_single_value("Accounts Settings", "merge_similar_account_heads")

        gl_map = self.build_gl_map()
        if self.voucher_type in ("Deferred Revenue", "Deferred Expense"):
            update_outstanding = "No"
        else:
            update_outstanding = "Yes"
            
        for d in self.accounts:
            if d.reference_type == 'Fees':
                update_outstanding = "No"
                break 
        

        if gl_map:
            make_gl_entries(
                gl_map,
                cancel=cancel,
                adv_adj=adv_adj,
                merge_entries=merge_entries,
                update_outstanding=update_outstanding,
            )
            if cancel:
                cancel_exchange_gain_loss_journal(frappe._dict(doctype=self.doctype, name=self.name))

    def on_submit(self):
        super(customJournalEntry, self).on_submit()
        if self.is_petty_cash and not self.petty_cash_approved:
            frappe.throw(_("Petty Cash Journal Entry must be approved before submission"))
