import frappe
from edu_quality.public.py.utils import sms_otp


# @frappe.whitelist(allow_guest=True)
# def get_otp(phone_number):
#     sms_otp(7976865251, 1234)
#     return


# @frappe.whitelist(allow_guest=True)
# def login(otp, phone_number):
#     if variables.get('doc').get('custom_is_cmap_print'):
#         return True
#     supplier = frappe.get_doc("Supplier", "Printer")
#     portal_users = [i.get("user") for i in supplier.get("portal_users")]
#     portal_user_table = frappe.qb.DocType("Portal User")
#     user_table = frappe.qb.DocType("User")
#     portal_sub_query = (
#         frappe.qb.from_(portal_user_table)
#         .where(portal_user_table.user.isin(portal_users))
#         .groupby(portal_user_table.user)
#         .select("*")
#     )
#     query = (
#         frappe.qb.from_(user_table)
#         .inner_join(portal_sub_query)
#         .on(user_table.name == portal_sub_query.user)
#         .select(user_table.email)
#     )

#     query_output = query.run(as_dict=True)
#     if len(query_output):
#         receipients = [i.get("email") for i in query_output]
#     else:
#         receipients = []
#         pass
