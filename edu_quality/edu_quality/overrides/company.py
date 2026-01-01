import frappe
from erpnext.setup.doctype.company.company import Company


ACCOUNT_HEADS = [
    {
        "account_name": "Event Collection",
        "parent_account_name": "Indirect Income",
    },
    {
        "account_name": "Discount",
        "parent_account_name": "Accounts Payable",
    },
    {
        "account_name": "Fee Advance",
        "parent_account_name": "Accounts Payable",
    },
    {
        "account_name": "Refundable Deposit",
        "parent_account_name": "Accounts Payable",
    },
    {
        "account_name": "Concession",
        "parent_account_name": "Accounts Payable",
    },
]


class CustomCompany(Company):
    def on_update(self):
        """
        This method creates the account heads for the company.
        """
        if hasattr(super(), "on_update"):
            super().on_update()
        self.create_account_heads()

    def create_account_heads(self):
        """
        This method creates the account heads for the company.
        """
        for account_head in ACCOUNT_HEADS:
            create_account_head(
                account_head["account_name"],
                account_head["parent_account_name"],
                self.name,
            )


def create_account_head(account_name, parent_account_name, company, account_type=None):
    """
    This method creates accounts for the company.
    """
    parent = frappe.get_value(
        "Account",
        {"account_name": parent_account_name, "company": company},
        "name",
    )

    if not parent:
        return

    if frappe.db.exists("Account", {"account_name": account_name, "company": company}):
        return

    account = frappe.get_doc(
        {
            "doctype": "Account",
            "account_name": account_name,
            "account_type": account_type,
            "company": company,
            "parent_account": parent,
        }
    )
    account.insert(ignore_permissions=True)


def delete_account_head(account_name, company):
    """
    This method deletes the specified account for the company if it exists.
    """
    # Directly attempt to delete the account without checking if it exists
    account_key = {"account_name": account_name, "company": company}
    existing_account = frappe.get_value("Account", account_key, "name")
    if existing_account:
        frappe.delete_doc("Account", existing_account)
        frappe.db.commit()
