import frappe

@frappe.whitelist()
def enqueue_gardian_user_creation():
    frappe.enqueue(create_users, queue='long', timeout=600000)
    return True

def create_users():
    try:
        guardians = frappe.get_all("Guardian", filters=[["Guardian","user","is","not set"]],fields=["name","email_address"])
        frappe.flags.in_import = True
        for guardian in guardians:
            if guardian.email_address:
                doc = frappe.get_doc("Guardian", guardian.name)
                try:
                    create_user(doc,patch=1)
                    set_student_permissions(doc)
                except Exception as e:
                    print(e)
        frappe.flags.in_import = False
    except Exception as e:
        frappe.logger('guardian_user').exception(e) 



def before_insert(doc,method=None):
    if validate_name(doc):
        create_user(doc)
        set_student_permissions(doc)

def on_update(doc,method=None):
    set_student_permissions(doc)


def validate_name(doc):
    if doc.guardian_name == "not picked":
        frappe.db.delete("Guardian",doc.name)
        return False 
    return True

def create_user(doc, patch=0):
    if not validate_name(doc):
        return
    
    if not (doc.email_address or doc.mobile_number):
       return

    email = doc.email_address if doc.email_address else doc.mobile_number + "@walnutedu.in"


    guardian_user = frappe.db.get_value("User", {"email": email})

    if guardian_user:
        doc.user = guardian_user
    else:
        try:
            user_doc = {
            "doctype": "User",
            "first_name": doc.guardian_name,
            "email": email,
            "roles": [{"role": "Guardian"}],
            "user_type": "System User",
            "send_welcome_email": 0
            }
            user = frappe.get_doc(user_doc).insert(ignore_permissions=True)
            doc.user = user.name
            if patch:
                doc.save(ignore_permissions=True)
        except Exception as e:  
            frappe.logger('guardian_user').exception(e)

def set_student_permissions(doc,patch=0):
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
            
