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
from edu_quality.edu_quality.server_scripts.payment_split import generate_split_payment
from frappe.desk.query_report import run


class CustomFees(Fees):
    @frappe.whitelist()
    def get_uncreated_payment_terms(self):
        terms = []
        for term in self.payment_schedule:
            if not frappe.db.exists("Payment Request",{'reference_name':self.name,'payment_term':term.payment_term,'docstatus':1}):
                terms.append(term.payment_term)
        return terms

    @frappe.whitelist()
    def create_payment_request(self,payment_term):
        if not payment_term:
            return frappe.throw("Invalid Payment Term!")
        elif frappe.db.exists("Payment Request",{'reference_name':self.name,'payment_term':payment_term,'docstatus':1}):
            return frappe.throw("Payment Request already created!")
        else:
            frappe.enqueue(
                "edu_quality.public.py.student.create_payment_request",
                fee=self,
                term = payment_term,
                is_async=True,
                queue="long",
                timeout=1800,
            )
            return frappe.msgprint("Payment Request Generation is enqueued!")
    
    def deduct_from_deposit(self,deposit_amount,deposit_account):
        if self.outstanding_amount <=deposit_amount:
            pending_fees = self.company_wise_pending_fees()
        else:
            remaining_deposit = 0
            company_list = self.company_wise_balance()
            split_amount = deposit_amount/len(company_list)
            for company in company_list:
                if company.get('balance') >= split_amount:
                    self.reverse_partial_amount(company.get('company'),split_amount,deposit=1)
                    company['balance'] -= split_amount
                else:
                    if company.get('balance') > 0:
                        self.reverse_partial_amount(company.get('company'),company.get('balance'),deposit=1)
                        remaining_deposit += split_amount - company.get('balance')
                        company['balance'] = 0 
            while remaining_deposit > 0:
                for company in company_list:
                    if company.get('balance') >= remaining_deposit:
                        self.reverse_partial_amount(company.get('company'),remaining_deposit,deposit=1)
                        company['balance'] -= remaining_deposit
                        remaining_deposit = 0
                    else:
                        self.reverse_partial_amount(company.get('company'),company.get('balance'),deposit=1)
                        remaining_deposit = remaining_deposit - company.get('balance')
                        company['balance'] = 0
            




    def generate_split(self):
        generate_split_payment(self)

    def update_split(self):
        generate_split_payment(self,update=1)
        
    def on_cancel(self):
        self.ignore_linked_doctypes = ("GL Entry", "Payment Ledger Entry","Journal Entry")
        make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)
        # frappe.db.set(self, 'status', 'Cancelled')

    def reverse_pending_fees(self):
        if not self.outstanding_amount < self.grand_total:
            return frappe.throw("Fees has not been paid!")
        return self.company_wise_pending_fees()
    
    def company_wise_balance(self):
        result = []
        company_list = frappe.get_all("Company")
        for company in company_list:
            company_doc = frappe.get_doc("Company",company.name)
            filter = {
                "company":company.name,
                "from_date":str(self.posting_date),
                "to_date":frappe.utils.nowdate(),
                "account":[company_doc.default_receivable_account],
                "party_type":"Student",
                "party":[self.student],
                "party_name":self.student,
                "group_by":"Group by Voucher (Consolidated)",
                "cost_center":[],
                "school":[],
                "program":[],
                "project":[],
                "include_dimensions":1,
                "include_default_book_entries":1,
                "show_remarks":1}
            report = run(report_name="General Ledger",filters=filter,user="Administrator")
            balance = report['result'][-1]['balance']
            result.append({"company":company,"balance":balance})
        return result
        
    def company_wise_pending_fees(self,deposit=0):
        result = self.company_wise_balance()
        for company in result:
            if company.get('balance') > 0:
                self.reverse_partial_amount(company.get('company'),company.get('balance'),deposit)
        return 1

    def reverse_partial_amount(self,company,amount,deposit):
        company = frappe.get_doc("Company",company.name)
        account = company.custom_default_concession_account
        if deposit:
            account = company.default_cash_account 

        je = frappe.new_doc("Journal Entry")
        je.update({
                    "is_system_generated": 1,
                    "title": "Fee Concession",
                    "voucher_type": "Journal Entry",
                    "naming_series": "ACC-JV-.YYYY.-",
                    "company": company.name,
                    "posting_date": frappe.utils.nowdate(),
                    "cheque_no": self.name,
                    "cheque_date": frappe.utils.nowdate(),
                    "user_remark": "Fee Concession",
                    "total_debit": amount,
                    "total_credit": amount,
                    "write_off_based_on": "Accounts Receivable",
                    "write_off_amount": 0,
                    "letter_head": "Default letter head",
                    "is_opening": "No",
                    "repost_required": 0,
                    "doctype": "Journal Entry",
        })
        je.append("accounts", 
                  {
                    "account": account,
                    "account_type": "Expense Account",
                    "cost_center": company.cost_center,
                    "account_currency": "INR",
                    "exchange_rate": 1,
                    "debit_in_account_currency": amount,
                    "debit": amount,
                    "credit_in_account_currency": 0,
                    "credit": 0,
                    "reference_type": "Fees",
                    "reference_name": self.name,
                    "reference_due_date": frappe.utils.nowdate(),
                    "is_advance": "No",
                    "user_remark": "Fee Concession",
                    "against_account": company.default_receivable_account
                    })
        je.append("accounts",
                  {
                        "account": company.default_receivable_account,
                        "account_type": "",
                        "party_type": "Student",
                        "party": self.student,
                        "cost_center": company.cost_center,
                        "account_currency": "INR",
                        "exchange_rate": 1,
                        "debit_in_account_currency": 0,
                        "debit": 0,
                        "credit_in_account_currency": amount,
                        "credit": amount,
                        "is_advance": "No",
                        "against_account": account
                        })
        je.save(ignore_permissions=True)
        je.submit()



    def deposit_adjustment_entry(self,amount):

        company = frappe.get_doc("Company",frappe.defaults.get_user_default("company"))

        je = frappe.new_doc("Journal Entry")
        je.update({
                    "is_system_generated": 1,
                    "title": "Deposit Adjustment",
                    "voucher_type": "Journal Entry",
                    "naming_series": "ACC-JV-.YYYY.-",
                    "company": company.name,
                    "posting_date": frappe.utils.nowdate(),
                    "cheque_no": self.name,
                    "cheque_date": frappe.utils.nowdate(),
                    "user_remark": "Deposit Adjustment",
                    "total_debit": amount,
                    "total_credit": amount,
                    "write_off_based_on": "Accounts Receivable",
                    "write_off_amount": 0,
                    "letter_head": "Default letter head",
                    "is_opening": "No",
                    "repost_required": 0,
                    "doctype": "Journal Entry",
        })
        je.append("accounts", 
                  {
                    "account": company.default_deposit_account,
                    "account_type": "Payable",
                    "cost_center": company.cost_center,
                    "account_currency": "INR",
                    "exchange_rate": 1,
                    "debit_in_account_currency": amount,
                    "debit": amount,
                    "credit_in_account_currency": 0,
                    "credit": 0,
                    "reference_type": "Fees",
                    "reference_name": self.name,
                    "reference_due_date": frappe.utils.nowdate(),
                    "is_advance": "No",
                    "user_remark": "Deposit Adjustment",
                    "against_account": company.default_cash_account
                    })
        je.append("accounts",
                  {
                        "account": company.default_cash_account,
                        "account_type": "Cash",
                        "party_type": "Student",
                        "party": self.student,
                        "cost_center": company.cost_center,
                        "account_currency": "INR",
                        "exchange_rate": 1,
                        "debit_in_account_currency": 0,
                        "debit": 0,
                        "credit_in_account_currency": amount,
                        "credit": amount,
                        "is_advance": "No",
                        "against_account": company.default_deposit_account
                        })

        je.save(ignore_permissions=True)
        je.submit()




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
            entries = []
            fee_advance_entries, fee_advance = get_fee_advance_entries(self)
            update_componant(self, fee_advance)
            student_entries = {}
            fee_entries = {}
            for component in self.components:
                receivable_account, sales,cost_center,deposit_account = frappe.db.get_value("Company", component.custom_company,["default_receivable_account","default_income_account","cost_center","default_deposit_account"])
                income_account = sales
                if "deposit" in str(component.fees_category).lower():
                        entries.append(self.get_gl_dict(
                                                {
                                                    "company": component.custom_company,
                                                    "account": receivable_account,
                                                    "party_type": "Student",
                                                    "party": self.student,
                                                    "against": deposit_account,
                                                    "debit": component.amount,
                                                    "debit_in_account_currency": component.amount,
                                                    "against_voucher": self.name,
                                                    "against_voucher_type": self.doctype
                                                },
                                                item=self,
                                            ))
                        entries.append(self.get_gl_dict(
                                        {
                                            "company": component.custom_company,
                                            "account": deposit_account,
                                            "against": self.student,
                                            "credit": component.amount,
                                            "credit_in_account_currency": component.amount,
                                            "cost_center": cost_center
                                        },
                                        item=self,
                                    ))
                        continue
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
            for i in student_entries.values():
                if int(i.get("debit")) == 0 and int(i.get("credit")) == 0:
                    continue
                entries.append(i)
            for j in fee_entries.values():
                if int(i.get("debit")) == 0 and int(i.get("credit")) == 0:
                    continue
                entries.append(j)
            entries.extend(fee_advance_entries if fee_advance_entries else [])
            return entries
        except Exception as e:
            frappe.logger('fee').exception(e)



def before_save(doc,method=None):
    update_fee_components(doc)
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
                    "school": component.school,
                    'label': component.label,
                    "doctype": "Fee Component"
                    })

def update_fee_components(doc):
    for component in doc.components:
        school = frappe.get_value("Fee Component",{"fees_category":component.fees_category, "parent": doc.fee_structure},'school')
        component.school = school
        

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
          

def get_fee_advance_entries(fees):
    fee_advance = frappe.db.get_value("Fee Advance",{"student":fees.student,"docstatus":1, "outstanding_amount":0, "next_program": fees.program, "academic_year":fees.academic_year},"name")
    if not fee_advance:
         return [], None
    gl_entries = frappe.db.get_all(
        "GL Entry",
        filters={
            "voucher_type": "Fee Advance",
            "voucher_no": fee_advance,
            "is_cancelled":0
        },
        fields=["account", "debit", "credit", "company", "against", "against_voucher", "against_voucher_type"],
    )
    student_entries = {}
    fee_entries = {}

    for entry in gl_entries:
        liability_account, income_account, cost_center = frappe.db.get_value("Company", entry.company,["default_liability_account", "default_income_account","cost_center"])
        student_entries[income_account] = (fees.get_gl_dict(
                                        {
                                            "company": entry.company,
                                            "account": liability_account,
                                            "party_type": "Student",
                                            "party": fees.student,
                                            "against": income_account,
                                            "debit": entry.credit if entry.credit else entry.debit,
                                            "debit_in_account_currency": entry.credit if entry.credit else entry.debit,
                                            "against_voucher": fees.name,
                                            "against_voucher_type": fees.doctype,
                                        },
                                        item=fees,
                                    ))
        
        fee_entries[liability_account] = (fees.get_gl_dict(
                        {
                            "company": entry.company,
                            "account": income_account,
                            "against": fees.student,
                            "credit": entry.credit if entry.credit else entry.debit,
                            "credit_in_account_currency": entry.credit if entry.credit else entry.debit,
                            "cost_center": cost_center
                        },
                        item=fees,
                    ))
             
        
    entries = []
    # for i in student_entries.values(): #financial rollover
    #     entries.append(i)
    # for j in fee_entries.values():
    #     entries.append(j)

    return entries, fee_advance


def update_componant(doc, fee_advance):
    if fee_advance:
        fee_advance = frappe.get_doc("Fee Advance", fee_advance)
        for item1, item2 in zip(doc.components, fee_advance.components):
            if item1.fees_category == item2.fees_category:
                item1.amount = item1.amount-item2.amount