import frappe

def execute():
    replace_emails()

def replace_emails():
    data = frappe.db.get_all("Guardian", fields=["name","email_address"])
    for guardian in data:
        if guardian.email_address:
            new_email = guardian.email_address.split("@")[0] + "@yopmail.com"
            frappe.db.set_value("Guardian",guardian.name,{"email_address":new_email,"mobile_number":""})
        else:
            frappe.db.set_value("Guardian",guardian.name,"mobile_number","")
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