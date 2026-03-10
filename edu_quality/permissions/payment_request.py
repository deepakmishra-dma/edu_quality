import frappe


def payment_request_query(user):

    permission_data = frappe.db.get_all(
        "User Permission", {"user": user}, ["for_value", "allow"]
    )
    tables = {}

    for perm in permission_data:
        table = perm["allow"]
        value = perm["for_value"]
        if table not in tables:
            tables[table] = [value]
        else:
            tables[table].append(frappe.db.escape(value))

    if not tables:
        return ""

    if tables:
        queries = []
        for table in tables:
            queries.append(
                f"""(`tabPayment Request`.`party_type`= {frappe.db.escape(table)} and `tabPayment Request`.`party` in {tuple(tables[table])})"""
            )
        return " or ".join(queries) or ""

    return ""
