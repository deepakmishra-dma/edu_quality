import frappe



@frappe.whitelist()
def manual_payment(fee,term,data):
    try:
        if frappe.db.exists("Payment Request",{'reference_name':fee,'payment_term':term}):
            frappe.db.set_value("Payment Request",{'reference_name':fee,'payment_term':term},'mode_of_payment',"Cheque")
            pr = frappe.get_doc("Payment Request",{'reference_name':fee,'payment_term':term})
            pr.set_as_paid()
            entries = frappe.get_all("Payment Entry", [["remark","Like",pr.name]],['name','company'])
            for entry in entries:
                for i in data:
                    if entry.company == i.company:
                        frappe.db.set_value("Payment Entry",entry.name,'reference_no',entry.reference_number)
    except Exception as e:
        frappe.logger("manual").exception(e)
        return e