import frappe

def execute():
    return
    replace_emails()

def replace_emails():
    data = frappe.db.get_all("Guardian", fields=["name","email_id"])
    for guardian in data:
        new_email = guardian.email_id.split("@")[0] + "@yopmail.com"
        frappe.db.set_value("Guardian",guardian.name,{"email_id":new_email,"mobile_number":""})
    student = frappe.db.get_all("Student", fields=["name","student_email_id"])
    for st in student:
        new_email = st.student_email_id.split("@")[0] + "@yopmail.com"
        frappe.db.set_value("Student",st.name,{
            "student_email_id":new_email,
            "student_mobile_number":"",
            "primary_contact":"",
            "whatsapp_number":"",
            })
        frappe.db.set_value("Student",st.name,)