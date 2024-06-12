import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

class CustomPaymentEntry(PaymentEntry):

    def get_discounts(self):
        referral_discount = 0
        other_discount = 0
        if self.reference_doctype == "Fees":
            fee = frappe.get_doc("Fees", self.reference_name)
            for component in fee.components:
                if component.custom_discounts:
                    if component.custom_company == self.company:
                        other_discount += component.custom_discount_amount

        if self.reference_doctype == "Fee Advance":
            fee = frappe.get_doc("Fee Advance", self.reference_name)
            for component in fee.components:
                if component.custom_discounts:
                    if component.custom_company == self.company:
                        other_discount += component.custom_discount_amount
            if fee.referral_amount:
                referral_discount += fee.referral_amount
        return {"Referral Discount": referral_discount, "Other Discount": other_discount}
    
    
    def get_components(self):
        if self.reference_doctype == "Fees":
            fee = frappe.get_doc("Fees", self.reference_name)
            return fee.components
        elif self.reference_doctype == "Fee Advance":
            fee = frappe.get_doc("Fee Advance", self.reference_name)
            return fee.components
        else:
            return []