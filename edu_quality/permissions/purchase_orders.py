import frappe


def purchase_query(user):
    user = frappe.session.user
    roles = frappe.get_roles(frappe.session.user)

    if "Printer" in roles and "Administrator" not in roles:
        supplier = frappe.qb.DocType("Supplier")
        portal_user = frappe.qb.DocType("Portal User")

        printer_parent_suppliers = (
            frappe.qb.from_(portal_user)
            .where((portal_user.user == user))
            .select(portal_user.parent)
            .inner_join(supplier)
            .on(supplier.name == portal_user.parent)
            .select(supplier.name.as_("name"))
        )
        printer_parent_suppliers = printer_parent_suppliers.run(as_dict=True)
        # printer_parent_suppliers = frappe.get_all(
        #     "Supplier",
        #     fields="`tabPortal User.user` `tabSupplier.name`",
        #     # filters=[["`tabPortal User.user`", "=", user]],
        #     debug=True,
        # )
        frappe.errprint(printer_parent_suppliers)
        suppliers = [supplier.get("name") for supplier in printer_parent_suppliers]
        frappe.errprint(suppliers)
        if not suppliers:
            return f"(`tabPurchase Order`.`supplier` = 'None')"
        frappe.errprint(tuple(suppliers))

        if len(suppliers) == 1:
            return (
                f"`tabPurchase Order`.`supplier`= '{suppliers[0]}'"  # noqa: ignore=E501
            )
        return (
            f"`tabPurchase Order`.`supplier` IN {tuple(suppliers)}"  # noqa: ignore=E501
        )
