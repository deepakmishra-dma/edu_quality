import frappe


def before_insert(doc,method=None):
    create_user(doc)
    set_student_permissions(doc)

def on_update(doc,method=None):
    set_student_permissions(doc)

def create_user(doc,patch=0):
    if not doc.email_address:
        frappe.throw("Please set Email Address")
    else:
        guardian_as_user = frappe.get_value("User", dict(email=doc.email_address))
        if guardian_as_user:
            doc.user = guardian_as_user
        else:
            user = frappe.get_doc(
                {
                    "doctype": "User",
                    "first_name": doc.guardian_name,
                    "email": doc.email_address,
                    "roles": [{"role": "Guardian"}],
                    "user_type": "Website User",
                    "send_welcome_email": 0
                    
                }
            ).insert(ignore_permissions=True)
            doc.user=user.name
        if patch:
            doc.save(ignore_permissions=True)

def set_student_permissions(doc,patch=0):
    return
    for student in doc.students:
        if frappe.db.exists("User Permission",{
            "user":doc.user,
            "allow": "Student",
            "for_value":student.student
        }):
            continue 
        else:
            frappe.get_doc({
                "doctype": "User Permission",
                "user":doc.user,
                "allow": "Student",
                "for_value":student.student
            }).insert(ignore_permissions=True)
            
