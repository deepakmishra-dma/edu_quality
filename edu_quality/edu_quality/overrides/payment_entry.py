import frappe 

from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from frappe.utils.data import flt 
import json


class CustomPaymentEntry(PaymentEntry):                
    def breakup(self,term):
        listed_components = [i.fee_category for i in self.fee_category]
        fees = frappe.get_doc('Fees',self.reference_name)
        breakups = []
        deposit=0
        schecule_breakup = {} 
        portion = 100
        if fees.doctype == 'Fees':
            for schedule in fees.payment_schedule:
                if schedule.payment_term == term:
                    portion = schedule.invoice_portion 
                    if 'deposit' in schedule.description.lower():
                        deposit = 1 
                    schecule_breakup = json.loads(schedule.discount_breakup) if schedule.discount_breakup else {}

        for component in fees.components:
            if not component.fees_category in listed_components:
                continue
            breakup = []
            amount = flt(component.amount*portion/100,2) 
            if fees.doctype == 'Fees':
                if not deposit and component.fee_type != 'Regular':
                    continue
                elif deposit and component.fee_type != 'Regular':
                    amount = flt(component.amount,2)
            company = component.custom_company
            if component.discount_breakup:
                component_breakup = json.loads(component.discount_breakup) if component.discount_breakup else {}
                for dis in component_breakup:
                    if dis in schecule_breakup:
                        dis_amount = flt(schecule_breakup[dis]['discount_amount'],2)
                        breakup.append({
                        'fees_category': "Discount- " + dis,
                        'amount':  frappe.utils.fmt_money(0-dis_amount, currency="INR"),
                        'company': company
                    })
            breakup = [{
                    'fees_category': component.fees_category,
                    'amount':  frappe.utils.fmt_money(amount, currency="INR"),
                    'company': company
                }] + breakup
            breakups = breakups + breakup
        return breakups
      
    def get_discounts(self):
        referral_discount = 0
        other_discount = 0
        ref_fee_head_check = False
        if self.reference_doctype == "Fees":
            pass
        if self.reference_doctype == "Fee Advance":
            fee = frappe.get_doc("Fee Advance", self.reference_name)
            for component in fee.components:
                if component.custom_company == self.company:
                    if component.fees_category=="Tuition Fee":
                        ref_fee_head_check = True
                    if component.custom_discounts:
                        other_discount += component.custom_discount_amount
            if fee.referral_amount and ref_fee_head_check:
                referral_discount += fee.referral_amount
            if component.custom_discounts:
                referral_discount = (other_discount-referral_discount)
        return {"Referral Discount": referral_discount, "Other Discount": referral_discount}
    
    
    def get_components(self):
        fee = frappe.get_doc("Fee Advance", self.reference_name)
        return fee.components
