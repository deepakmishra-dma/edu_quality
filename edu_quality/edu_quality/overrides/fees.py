import frappe 
import erpnext
from education.education.doctype.fees.fees import Fees
from erpnext.accounts.utils import get_account_currency, get_fiscal_years, validate_fiscal_year
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)
from frappe.utils import (
    add_days,
    add_months,
    cint,
    flt,
    fmt_money,
    formatdate,
    get_last_day,
    get_link_to_form,
    getdate,
    nowdate,
    today,
)
from frappe import _, bold, throw
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.general_ledger import make_reverse_gl_entries


class CustomFees(Fees):
    def make_gl_entries(self):
        if not self.grand_total:
            return
        entries = self.get_company_splits()
        

        make_gl_entries(
            entries,
            cancel=(self.docstatus == 2),
            update_outstanding="No",
            merge_entries=False,
        )
    
    def get_gl_dict(self, args, account_currency=None, item=None):
        """this method populates the common properties of a gl entry record"""
        company = args.get('company') or self.company
        posting_date = args.get("posting_date") or self.get("posting_date")
        fiscal_years = get_fiscal_years(posting_date, company=company)
        if len(fiscal_years) > 1:
            frappe.throw(
                _("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
                    formatdate(posting_date)
                )
            )
        else:
            fiscal_year = fiscal_years[0][0]

        gl_dict = frappe._dict(
            {
                "company": company,
                "posting_date": posting_date,
                "fiscal_year": fiscal_year,
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "remarks": self.get("remarks") or self.get("remark"),
                "debit": 0,
                "credit": 0,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": 0,
                "is_opening": self.get("is_opening") or "No",
                "party_type": None,
                "party": None,
                "project": self.get("project"),
                "post_net_value": args.get("post_net_value"),
            }
        )

        update_gl_dict_with_regional_fields(self, gl_dict)
        accounting_dimensions = get_accounting_dimensions()
        dimension_dict = frappe._dict()

        for dimension in accounting_dimensions:
            dimension_dict[dimension] = self.get(dimension)
            if item and item.get(dimension):
                dimension_dict[dimension] = item.get(dimension)

        gl_dict.update(dimension_dict)
        gl_dict.update(args)

        if not account_currency:
            account_currency = get_account_currency(gl_dict.account)

        if gl_dict.account and self.doctype not in [
            "Journal Entry",
            "Period Closing Voucher",
            "Payment Entry",
            "Purchase Receipt",
            "Purchase Invoice",
            "Stock Entry",
        ]:
            self.validate_account_currency(gl_dict.account, account_currency)

        if gl_dict.account and self.doctype not in [
            "Journal Entry",
            "Period Closing Voucher",
            "Payment Entry",
        ]:
            set_balance_in_account_currency(
                gl_dict, account_currency, self.get("conversion_rate"), self.company_currency
            )

        return gl_dict
    
    def remove_discount_entry(self,company,amount):
        receivable_account, discount_account = frappe.db.get_value("Company", company,["default_receivable_account","default_discount_account"])
        entries = []
        debit_filter = {'voucher_type':self.doctype,'voucher_no':self.name,'account':receivable_account,'debit':amount}
        credit_filter = {'voucher_type':self.doctype,'voucher_no':self.name,'account':discount_account,'credit':amount}
        if frappe.db.exists("GL Entry",debit_filter):
            entries.append(frappe.get_doc("GL Entry",debit_filter).as_dict())
        if frappe.db.exists("GL Entry",credit_filter):
            entries.append(frappe.get_doc("GL Entry",credit_filter).as_dict())
        make_reverse_gl_entries(entries)
         
    def add_discount_entry(self,company,amount):
        receivable_account, discount_account, cost_center = frappe.db.get_value("Company", company,["default_receivable_account","default_discount_account","cost_center"])
        debit_entry = (self.get_gl_dict(
                {
                    "company": company,
                    "account":discount_account ,
                    "party_type": "Student",
                    "party": self.student,
                    "against": receivable_account,
                    "debit": amount,
                    "debit_in_account_currency": amount,
                    "against_voucher": self.name,
                    "against_voucher_type": self.doctype
                },
                item=self,
            ))
        credit_entry = (self.get_gl_dict(
                        {
                            "company": company,
                            "account": receivable_account,
                            "against": self.student,
                            "credit": amount,
                            "credit_in_account_currency":amount,
                            "cost_center": cost_center
                        },
                        item=self,
                    ))
        make_gl_entries(
        [debit_entry,credit_entry],
        cancel=(self.docstatus == 2),
        update_outstanding="No",
        merge_entries=False,
    )
    
    
         

    
    def get_company_splits(self):
        try:
            student_entries = {}
            fee_entries = {}
            for component in self.components:
                receivable_account, income_account,cost_center = frappe.db.get_value("Company", component.custom_company,["default_receivable_account","default_income_account","cost_center"])
                if receivable_account in student_entries:
                    student_entries[receivable_account].debit += component.amount
                    student_entries[receivable_account].debit_in_account_currency += component.amount
                    fee_entries[income_account].credit += component.amount 
                    fee_entries[income_account].credit_in_account_currency += component.amount 
                else:
                    student_entries[receivable_account] = (self.get_gl_dict(
                                                {
                                                    "company": component.custom_company,
                                                    "account": receivable_account,
                                                    "party_type": "Student",
                                                    "party": self.student,
                                                    "against": income_account,
                                                    "debit": component.amount,
                                                    "debit_in_account_currency": component.amount,
                                                    "against_voucher": self.name,
                                                    "against_voucher_type": self.doctype
                                                },
                                                item=self,
                                            ))
                    fee_entries[income_account] = (self.get_gl_dict(
                                    {
                                        "company": component.custom_company,
                                        "account": income_account,
                                        "against": self.student,
                                        "credit": component.amount,
                                        "credit_in_account_currency": component.amount,
                                        "cost_center": cost_center
                                    },
                                    item=self,
                                ))
            entries = []
            for i in student_entries.values():
                entries.append(i)
            for j in fee_entries.values():
                entries.append(j)
            return entries
        except Exception as e:
            frappe.logger('fee').exception(e)



def before_save(doc,method=None):
    is_rte = frappe.get_value("Student",doc.student,'is_rte')
    if not is_rte:
        return 
    components = doc.components
    doc.components=[]
    for component in components:
        if component.rte_excempt:
            continue
        doc.append('components',
                    {
                    "fees_category": component.fees_category,
                    "amount":component.amount,
                    "custom_discounts": component.custom_discounts,
                    "custom_discount_percentage": component.custom_discount_percentage,
                    "custom_discount_amount": component.custom_discount_amount,
                    "custom_amount_after_discount": component.custom_amount_after_discount,
                    "fee_type": component.fee_type,
                    "custom_company": component.custom_company,
                    "rte_excempt": 0,
                    "doctype": "Fee Component"
                    })

        

@erpnext.allow_regional
def update_gl_dict_with_regional_fields(doc, gl_dict):
	pass

def set_balance_in_account_currency(
	gl_dict, account_currency=None, conversion_rate=None, company_currency=None
):
	if (not conversion_rate) and (account_currency != company_currency):
		frappe.throw(
			_("Account: {0} with currency: {1} can not be selected").format(
				gl_dict.account, account_currency
			)
		)

	gl_dict["account_currency"] = (
		company_currency if account_currency == company_currency else account_currency
	)

	# set debit/credit in account currency if not provided
	if flt(gl_dict.debit) and not flt(gl_dict.debit_in_account_currency):
		gl_dict.debit_in_account_currency = (
			gl_dict.debit
			if account_currency == company_currency
			else flt(gl_dict.debit / conversion_rate, 2)
		)

	if flt(gl_dict.credit) and not flt(gl_dict.credit_in_account_currency):
		gl_dict.credit_in_account_currency = (
			gl_dict.credit
			if account_currency == company_currency
			else flt(gl_dict.credit / conversion_rate, 2)
		)