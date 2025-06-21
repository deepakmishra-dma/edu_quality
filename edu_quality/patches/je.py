import frappe 


#sales to fee advance
companies =["Unique Educational and Sports Foundation","Rethink Educational Services LLP"]

for company in companies:
    fee_advance_to_sale_entries = frappe.db.get_all("GL Entry",filters=[["GL Entry","account","like","%Fee Advance%"],["GL Entry","against","like","%Sales%"],["GL Entry","company","=",company]],fields=["name","account","party_type","party","debit","debit_in_account_currency","against","against_voucher_type","against_voucher","voucher_type","voucher_no","program"])
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = company
    je.posting_date = frappe.utils.nowdate()
    total = 0.0
    for entry in fee_advance_to_sale_entries:
        log(entry.name)
        log(entry.debit_in_account_currency)
        je.append("accounts",{
            "account":entry.account,
            "credit_in_account_currency":entry.debit_in_account_currency,
            "party_type":entry.party_type,
            "party":entry.party,
            "reference_type":"Fees",
            "reference_name":entry.voucher_no,
            "is_advance":"Yes"
        })
        total = total + entry.debit_in_account_currency
    log(total)
    je.append("accounts",{
        "account":entry.against,
        "debit_in_account_currency":total
    })
    je.save(ignore_permissions=True)


#Debtors to sales
companies =["Unique Educational and Sports Foundation","Rethink Educational Services LLP","Little Nuts LLP"]

liability_map = {
    "Unique Educational and Sports Foundation": "Fee Advance - UESF",
    "Rethink Educational Services LLP": "Fee Advance - RESPL",
    "Little Nuts LLP": "Fee Advance - LNL"
}

for company in companies:
    fee_advance_to_sale_entries = frappe.db.get_all("GL Entry",filters=[["GL Entry","account","like","%Debtors%"],["GL Entry","against","like","%Sales%"],["GL Entry","company","=",company]],fields=["name","account","party_type","party","debit","debit_in_account_currency","against","against_voucher_type","against_voucher","voucher_type","voucher_no","program"])
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = company
    je.posting_date = frappe.utils.nowdate()
    total = 0.0
    for entry in fee_advance_to_sale_entries:
        if not frappe.db.get_value("Fees",entry.voucher_no,'docstatus')==2:
            je.append("accounts",{
                "account":liability_map[company],
                "credit_in_account_currency":entry.debit_in_account_currency,
                "party_type":entry.party_type,
                "party":entry.party,
                "reference_type":"Fees",
                "reference_name":entry.voucher_no,
                "is_advance":"Yes"
            })
            total = total + entry.debit_in_account_currency
    je.append("accounts",{
        "account":entry.against,
        "debit_in_account_currency":total
    })
    je.save(ignore_permissions=True)