import frappe


@frappe.whitelist()
def add_discount(fee_name, discount):
    fees = frappe.get_doc("Fees", fee_name)
    dis = frappe.get_doc("Discount Configuration", discount)

    for component in fees.components:
        if component.fees_category == dis.fee_category:
            discount_name = component.custom_discounts
            if discount_name and dis.can_be_applied_with_other_discounts == 1:
                discount_list = get_discount_list(discount_name)
                # if the discount is already present and the new discount could be applied with other discounts
                if dis.name not in discount_list:
                    discount_list.append(dis.name)
                    discount_name = ", ".join(discount_list)
                    if dis.discount_amount:
                        grand_discount_amount = dis.discount_amount
                        discounted_amount = grand_discount_amount + component.custom_discount_amount
                        amount = component.amount - discounted_amount
                        discount = calculate_discount(component.amount, discounted_amount)
                        update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees)
                        message = dis.name + " Discount applied successfully"
                        frappe.response['message'] = message
                    else:
                        amount = component.amount
                        grand_discount_amount = (amount * float(dis.discount)) / 100
                        discounted_amount = grand_discount_amount + component.custom_discount_amount
                        discount = calculate_discount(component.amount, discounted_amount)
                        amount = amount - discounted_amount
                        update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees)
                        message = dis.name + " Discount applied successfully"
                        frappe.response['message'] = message
                else:
                    frappe.response['message'] = "Discount already applied"
            elif discount_name and dis.can_be_applied_with_other_discounts == 0:
                discount_list = get_discount_list(discount_name)
                if dis.name in discount_list:
                    message = dis.name + " Discount already present"
                    frappe.response['message'] = message
                else:
                    message = dis.name + " Discount can not be applied with other discounts"
                    frappe.response['message'] = message
                # if the discount is already present and the new discount could not be applied with other discounts
            else:
                # if the discount is not already present
                discount_name = dis.name
                if dis.discount_amount:
                    discounted_amount = grand_discount_amount = dis.discount_amount
                    amount = component.amount - discounted_amount
                    discount = calculate_discount(component.amount, discounted_amount)
                    update_component(component.name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees)
                    message = dis.name + " Discount applied successfully"
                    frappe.response['message'] = message
                else:
                    grand_discount_amount = (component.amount * float(dis.discount)) / 100
                    discounted_amount = grand_discount_amount
                    amount = component.amount - discounted_amount
                    update_component(component.name, discount_name, dis.discount, discounted_amount, grand_discount_amount, amount, fees)
                    message = dis.name + " Discount applied successfully"
                    frappe.response['message'] = message


#remove discount
@frappe.whitelist()
def remove_discount(fee_name, discount):
    fees = frappe.get_doc("Fees", fee_name)
    dis = frappe.get_doc("Discount Configuration", discount)

    for component in fees.components:
        if component.custom_discounts:
            discount_list = get_discount_list(component.custom_discounts)
            if component.fees_category == dis.fee_category and discount in discount_list:
                grand_discount_amount = (component.amount * float(dis.discount)) / 100
                amount = component.custom_amount_after_discount + grand_discount_amount
                discount_amount = component.custom_discount_amount - grand_discount_amount
                discount = calculate_discount(component.amount, discount_amount)
                discount_list.remove(dis.name)
                discount_name = ", ".join(discount_list)
                # updating the data in the database
                remove_and_update_component(component.name, discount_name, discount, discount_amount, grand_discount_amount, amount, fees)
                message = dis.name + " Discount removed successfully"
                frappe.response['message'] = message
            elif discount not in discount_list:
                message = dis.name + " Discount does not present"
                frappe.response['message'] = message


def get_discount_list(input_string):
    split_strings = input_string.split(',')
    stripped_values = [value.strip() for value in split_strings]
    return stripped_values


def calculate_discount(amount, discounted_amount):
    discount = 100 - ((amount - discounted_amount) / amount) * 100
    return discount

# updating the data in the database
def update_component(component_name, discount_name, final_discount, discounted_amount, grand_discount_amount, amount, fees):
    frappe.db.set_value("Fee Component", component_name, "custom_discounts", discount_name)
    frappe.db.set_value("Fee Component", component_name, "custom_discount_percentage", final_discount)
    frappe.db.set_value("Fee Component", component_name, "custom_discount_amount", discounted_amount)
    frappe.db.set_value("Fee Component", component_name, "custom_amount_after_discount", amount)
    grand_total = fees.grand_total - grand_discount_amount
    grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
    frappe.db.set_value("Fees", fees.name, "grand_total", grand_total)
    frappe.db.set_value("Fees", fees.name, "grand_total_in_words", grand_total_in_words)
    frappe.db.set_value("Fees", fees.name, "outstanding_amount", grand_total)


def remove_and_update_component(component_name, discount_name, discount, discounted_amount, grand_discount_amount, amount, fees):
    frappe.db.set_value("Fee Component", component_name, "custom_discounts", discount_name)
    frappe.db.set_value("Fee Component", component_name, "custom_discount_percentage", discount)
    frappe.db.set_value("Fee Component", component_name, "custom_amount_after_discount", amount)
    if discounted_amount:
        frappe.db.set_value("Fee Component", component_name, "custom_discount_amount", discounted_amount)
        grand_total = fees.grand_total + grand_discount_amount
    else:
        frappe.db.set_value("Fee Component", component_name, "custom_discount_amount", 0)
        grand_total = fees.grand_total + grand_discount_amount

    grand_total_in_words = str(frappe.utils.in_words(grand_total)).title()
    frappe.db.set_value("Fees", fees.name, "grand_total", grand_total)
    frappe.db.set_value("Fees", fees.name, "grand_total_in_words", grand_total_in_words)
    frappe.db.set_value("Fees", fees.name, "outstanding_amount", grand_total)