import frappe
import requests
from frappe.utils import today
from edu_quality.api.google_admin import add_user_to_group, create_google_user


def after_insert(doc):
    """
    1. Create a Google User
    2. Create an Employee in Greythr
    3. Add to relevant groups on google workspace
    4. Add to relevant email groups in ERPNext
    5. Send Communication mails to the user
    """
    org_unit_path = get_google_group_info(doc.designation, info_type="org_unit_path")
    org_unit_path = f"/{doc.branch}/{org_unit_path}" if org_unit_path else None
    # Create a Google User
    res = create_google_user(
        doc.first_name,
        doc.first_name,
        doc.last_name,
        doc.personal_email,
        doc.cell_number,
        doc.branch,
        org_unit_path=org_unit_path,
    )
    doc.company_email = res.get("primaryEmail")
    doc.save()
    doc.reload()
    # Create an Employee in Greythr
    create_employee_in_greathr(doc)
    # Add to relevant groups on google workspace

    group_email = get_google_group_info(doc.designation, info_type="group_email")
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
    for eg in doc.employee_email_group:
        email_group = frappe.get_doc(
            {
                "doctype": "Email Group Member",
                "email_group": eg.email_group,
                "email": doc.company_email,
            }
        )
        email_group.insert(ignore_permissions=True)


def get_google_group_info(designation, info_type="org_unit_path"):
    """
    Get the google group information based on the info_type
    """
    google_service = frappe.get_single("Google Service Account")
    if not google_service:
        return
    group = next(
        (g for g in google_service.google_groups if g.role == designation), None
    )
    return (
        (group.group_email if info_type == "group_email" else group.org_unit_path)
        if group
        else None
    )
