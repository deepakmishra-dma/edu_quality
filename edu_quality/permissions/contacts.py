import frappe


def contact_query(user): 
    user = frappe.session.user
    roles = frappe.get_roles(frappe.session.user)
    if "Councellor" in roles and "Administrator" not in roles:
        if frappe.get_value("User Permission",{"user":user,"allow":"School"}):
            all_lead = frappe.get_list("Lead","fathers_phone")
            all_lead_con = [p.fathers_phone for p in all_lead]
            if not all_lead_con:
                return f"""(`tabContact`.`mobile_no` = 'None')"""  # noqa: ignore=E501

            if len(all_lead_con) == 1:
                return f"""(`tabContact`.`mobile_no` = '{all_lead_con[0]}')"""  # noqa: ignore=E501

            return f"""(`tabContact`.`mobile_no` in {tuple(all_lead_con)})"""  # noqa: ignore=E501