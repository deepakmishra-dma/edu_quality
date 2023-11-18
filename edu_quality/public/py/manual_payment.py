import frappe


@frappe.whitelist()
def manual_payment(fee,term,data):
    try:
        data = frappe.parse_json(data)
        if frappe.db.exists("Payment Request",{'reference_name':fee,'payment_term':term}):
            frappe.db.set_value("Payment Request",{'reference_name':fee,'payment_term':term},'mode_of_payment',"Cheque")
            pr = frappe.get_doc("Payment Request",{'reference_name':fee,'payment_term':term})
            pr.set_as_paid()
            entries = frappe.get_all("Payment Entry", {"reference_no": pr.name},['name','company', 'party', 'paid_amount'])
            for entry in entries:
                for i in data:
                    if entry.company == i.get("company"):
                        reference_no = i.get("reference_number")
                        update_reference(reference_no, entry)

        frappe.response["message"] = "Manual Payment Done"
    except Exception as e:
        frappe.logger("manual").exception(e)
        frappe.response["message"] = "Manual Payment Failed"
        return e


def update_reference(reference_no, entry):
    date = frappe.utils.nowdate()
    remarks = f"Amount INR {entry.paid_amount} received from {entry.party} Transaction reference no {reference_no} dated {date}"
    frappe.db.set_value("Payment Entry", entry.name, "reference_no", reference_no)
    frappe.db.set_value("Payment Entry", entry.name, "reference_date", date)
    frappe.db.set_value("Payment Entry", entry.name, "remarks", remarks)