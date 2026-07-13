import base64

import frappe
from frappe.utils.file_manager import save_file


@frappe.whitelist()
def petty_cash_submit(data):
	try:
		data = frappe.parse_json(data)
		account = get_data(data, "accountHead")
		company = get_data(data, "company")
		school = get_data(data, "school")
		amount = data.get("amount")
		to_from = data.get("to_from")
		description = data.get("description")
		_type = data.get("type")
		file = data.get("file")

		to_account, entry_type = determine_accounts_and_entry_type(company, school, _type)

		remark_parts = {}

		if description:
			remark_parts["Description"] = description

		if school:
			remark_parts["School"] = school

		remark = frappe.as_json(remark_parts)

		journal_entry = create_journal_entry(account, to_account, amount, entry_type, to_from, remark)

		# Save the file in the Journal Entry as an attachment
		handle_file(file, journal_entry)
		journal_entry.save()
		journal_entry.reload()

		return {
			"success": True,
			"data": journal_entry.as_dict(),
		}
	except Exception as e:
		frappe.log_error("Error in petty_cash_submit", frappe.get_traceback())
		return {
			"success": False,
			"data": str(e),
		}


def get_data(data, key):
	field = data.get(key)
	if isinstance(field, dict):
		field = field.get("name")
	return field


def determine_accounts_and_entry_type(company, school, _type):
	entry_type = "Cash Entry" if _type == "payment" else "Bank Entry"
	to_account = None
	if school:
		if _type == "payment":
			to_account = frappe.get_value("School", school, "petty_cash_account")
		else:
			to_account = frappe.get_value("School", school, "petty_cash_bank_account")
	if company and not to_account:
		if _type == "payment":
			to_account = frappe.get_value("Company", company, "default_petty_cash")
		else:
			to_account = frappe.get_value("Company", company, "default_petty_cash_bank")
	return to_account, entry_type


def handle_file(file_data, journal_entry):
	if file_data:
		file_data = file_data[0]
		file_content = base64.b64decode(file_data["url"].split(",")[1])
		filename = file_data["name"]
		return save_file(
			filename,
			file_content,
			dt=journal_entry.doctype,
			dn=journal_entry.name,
			folder="Home",
		)
	return None


def create_journal_entry(from_account, to_account, amount, entry_type, to_from, remark):
	"""
	Create a journal entry in the system.

	Parameters:
	from_account (str): The account from which the amount is debited.
	to_account (str): The account to which the amount is credited.
	amount (float): The amount to be transferred.
	entry_type (str): The type of the journal entry (e.g., 'Bank Entry', 'Cash Entry').
	to_from (str): The name of the person to whom the amount is transferred.
	remark (str): The remark for the journal entry.

	Returns:
	doc: The created Journal Entry document.
	"""
	journal_entry_data = {
		"doctype": "Journal Entry",
		"voucher_type": entry_type,
		"posting_date": frappe.utils.nowdate(),
		"accounts": [
			{"account": from_account, "debit_in_account_currency": amount},
			{"account": to_account, "credit_in_account_currency": amount},
		],
		"pay_to_recd_from": to_from,
		"user_remark": remark,
		"is_petty_cash": True,
	}

	# Add cheque details only for 'Bank Entry'
	if entry_type == "Bank Entry":
		journal_entry_data.update(
			{
				"cheque_no": "NA",
				"cheque_date": frappe.utils.nowdate(),
			}
		)

	journal_entry = frappe.get_doc(journal_entry_data)
	journal_entry.insert()
	return journal_entry
