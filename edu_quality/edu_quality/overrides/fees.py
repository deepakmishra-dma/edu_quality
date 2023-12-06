import frappe 


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

        