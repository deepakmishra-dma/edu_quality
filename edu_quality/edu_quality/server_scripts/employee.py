import re
import frappe
import requests
from frappe.utils import today
from edu_quality.api.google_admin import add_user_to_group, get_google_admin_object


def after_insert(doc, method=None):
    """
    1. Create a Google User
    2. Create an Employee in Greythr
    3. Add to relevant groups on google workspace
    4. Add to relevant email groups in ERPNext
    5. Send Communication mails to the user
    """
    # Create a Google User
    create_google_user_account(doc)
    # Create User in Frappe/ERPNext
    create_user(doc)
    # Create an Employee in Greythr
    create_employee_in_greathr(doc)
    # Add to relevant groups on google workspace

    # Get the google group email
    group_email = get_google_group_info(doc, info_type="group_email")
    if group_email:
        add_user_to_group(doc.company_email, group_email=group_email)

    # Add to relevant email groups in ERPNext
    add_to_email_group(doc)
    # Send Communication mails to the user
    try:
        from nextai.funnel.custom_trigger import trigger_event

        trigger_event(doc, "employee_created")
    except:
        frappe.log_error(
            f"Error while sending communication mail to the user",
            frappe.get_traceback(),
        )


def create_employee_in_greathr(doc):
    """
    Create an employee in Greythr
    """
    try:
        url = "https://api.greythr.com/employee/v2/employees"

        payload = {
            "employeeNo": doc.name,
            "name": doc.first_name,
            "firstName": doc.first_name,
            "middleName": doc.middle_name,
            "lastName": doc.last_name,
            "email": doc.company_email,
            "dateOfBirth": doc.date_of_birth,
            "dateOfJoin": today(),
            "gender": doc.gender,
            "mobile": doc.cell_number,
            "personalEmail": doc.personal_email,
            "officialMobile": doc.cell_number,
        }
        headers = {
            "ACCESS-TOKEN": "74ae0195-dd19-4d7c-948f-46dc592d888b",
            "x-greythr-domain": "uniqueeducational.greythr.com",
        }

        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
    except:
        frappe.log_error(
            f"Error while creating employee in Greythr", frappe.get_traceback()
        )


def add_to_email_group(doc):
    """
    Add the employee to the email group in ERPNext
    """
    for eg in doc.email_groups:
        email_group = frappe.get_doc(
            {
                "doctype": "Email Group Member",
                "email_group": eg.email_group,
                "email": doc.company_email,
            }
        )
        email_group.insert(ignore_permissions=True)


def get_google_group_info(doc, info_type="org_unit_path"):
    """
    Get the google group information based on the info_type
    """
    school = frappe.get_doc("School", doc.branch)
    group = next(
        (g for g in school.google_groups if g.role == doc.designation), None
    )
    return (
        (group.group_email if info_type == "group_email" else group.org_unit_path)
        if group
        else None
    )


def create_google_user_account(doc):
    """
    Create a google user account
    """
    org_unit_path = get_google_group_info(doc)
    org_unit_path = f"/{doc.branch}/{org_unit_path}" if org_unit_path else None
    email_key = doc.employee_name.lower().strip().replace(" ", ".")
    # Create a Google User
    company_email = create_employee_google_user(
        email_key,
        doc.first_name,
        doc.last_name,
        doc.personal_email,
        doc.cell_number,
        doc.branch,
        org_unit_path=org_unit_path,
    )
    doc.company_email = company_email
    doc.save()
    doc.reload()


def create_user(emp):
    employee_name = emp.employee_name.split(" ")
    middle_name = last_name = ""

    if len(employee_name) >= 3:
        last_name = " ".join(employee_name[2:])
        middle_name = employee_name[1]
    elif len(employee_name) == 2:
        last_name = employee_name[1]

    first_name = employee_name[0]

    user = frappe.new_doc("User")
    user.update(
        {
            "name": emp.employee_name,
            "email": emp.company_email,
            "enabled": 1,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "gender": emp.gender,
            "birth_date": emp.date_of_birth,
            "phone": emp.cell_number,
            "bio": emp.bio,
        }
    )
    user.append("roles", {
        "role": emp.role
    })
    user.insert()
    emp.user_id = user.name
    emp.save()
    emp.reload()


def create_employee_google_user(
    email_key, first_name, last_name, recovery_mail, phone_no, school, org_unit_path=None
):
    user_service = get_google_admin_object()
    
    existing_user = None
    for i in range(4):
        existing_user = get_existing_google_user(email_key)
        if not existing_user:
            break
        email_key += str(i)

    company_email = f"{email_key}@walnutedu.in"
    
    if not existing_user:
        recovery_mail = (str(recovery_mail) or "feedback@walnutedu.in").strip().lower()
        email_pattern = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        recovery_mail = "feedback@walnutedu.in" if not re.match(email_pattern, recovery_mail) else recovery_mail
        
        new_user = {
            "primaryEmail": company_email,
            "name": {
                "givenName": first_name,
                "familyName": last_name,
            },
            "password": "walnut@12345",
            "changePasswordAtNextLogin": True,
            "ipWhitelisted": False,
            "recoveryEmail": recovery_mail,
            "orgUnitPath": org_unit_path or f"/{school}/Students",
        }
        
        frappe.log_error("account creating for ", str(new_user))
        resp = (
            user_service.users()
            .insert(
                body=new_user,
            )
            .execute()
        )
        frappe.log_error("Account created for ", str(resp))
        return company_email


def get_existing_google_user(email_key):
    user_service = get_google_admin_object()
    try:
        return (
            user_service.users()
            .get(
                userKey=f"{email_key}@walnutedu.in",
            )
            .execute()
        )
    except:
        return None