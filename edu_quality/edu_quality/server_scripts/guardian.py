import frappe

@frappe.whitelist()
def enqueue_gardian_user_creation():
    frappe.enqueue(create_users, queue='long')
    return True

def create_users():
    try:
        guardians = frappe.get_all("Guardian", filters=[["Guardian","user","is","not set"]],fields=["name","email_address"],limit=100)
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
            user_doc = frappe.new_doc("User")
            user_doc.first_name = doc.guardian_name
            user_doc.email = email
            user_doc.user_type = "System User"
            user_doc.append("roles", {"role": "Guardian"})
            user_doc.send_welcome_email = 0
            user_doc.insert(ignore_permissions=True)
            doc.user = user_doc.name
        except Exception as e:  
            frappe.logger('guardian_user').exception(e)
    if patch:
        doc.save(ignore_permissions=True)
        

def set_student_permissions(doc,patch=0):
    #student permissions
    for student in doc.students:
        if frappe.db.exists("User Permission",{
            "user":doc.user,
            "allow": "Student",
            "for_value":student.student
        }):
            continue 
        else:
            perm = frappe.new_doc("User Permission")
            perm.user = doc.user
            perm.allow = "Student"
            perm.for_value = student.student
            perm.insert(ignore_permissions=True)
    #applicant permissions
    applicants = frappe.db.get_all("Student Guardian",{'guardian':doc.name,'parenttype':"Student Applicant"},"parent")
    for applicant in applicants:
        if not frappe.db.exists("User Permission",{"user":doc.user,"allow":"Student Applicant","for_value":applicant.parent}):
            perm = frappe.new_doc("User Permission")
            perm.user = doc.user
            perm.allow = "Student Applicant"
            perm.for_value = applicant.parent
            perm.insert(ignore_permissions=True)
            
