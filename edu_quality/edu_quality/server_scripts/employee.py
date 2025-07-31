import re
import frappe
from frappe.utils.data import cint
from edu_quality.api.google_admin import (
    add_user_to_group,
    get_google_admin_object,
    suspend_google_user,
    get_google_user_with_key,
)

def before_save(doc, method=None):
    email_pattern = re.compile(r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?")
    mobile_pattern = re.compile(r"^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$")
    if not mobile_pattern.match(doc.cell_number):
        frappe.throw("Invalid Mobile Number")
    if not email_pattern.match(doc.personal_email):
        frappe.throw("Invalid Personal Email")


def after_insert(doc, method=None):
    """
    1. Create a Google User Account if the option is enabled
    2. Add to relevant groups on google workspace if the option is enabled
    3. Add to relevant email groups in ERPNext
    4. Send Communication mails to the user
    """
    create_employee_workspace = frappe.get_value("Google Service Account", None, "create_employee_workspace")
    if cint(create_employee_workspace):
        # Create a Google User
        create_google_user_account(doc)
        # Get the google group email
        group_email = get_google_group_info(doc, info_type="group_email")
        if group_email:
            add_user_to_group(doc.company_email, group_email=group_email)

    # Create User in Frappe/ERPNext
    create_user(doc)

    if doc.user_id:
        # Add to relevant email groups in ERPNext
        add_to_email_group(doc)
        # Add user permissions for the employee based on the schools
        add_to_user_permission(doc)
    # Send Communication mails to the user
    try:
        from nextai.funnel.custom_trigger import trigger_event
        trigger_event(doc, "employee_created")
    except:
        frappe.log_error(
            f"Error while sending communication mail to the user",
            frappe.get_traceback(),
        )


def before_insert(doc, method=None):
    create_employee_workspace = frappe.get_value("Google Service Account", None, "create_employee_workspace")
    if not cint(create_employee_workspace):
        doc.prefered_contact_email = 'Personal Email'


def on_update(doc, method=None):
    add_to_email_group(doc)
    add_to_user_permission(doc)


def add_to_email_group(doc):
    """
    Add the employee to the email group in ERPNext
    """
    remove_from_email_group(doc)
    for eg in doc.email_groups:
        email_group = frappe.get_doc(
            {
                "doctype": "Email Group Member",
                "email_group": eg.email_group,
                "email": doc.company_email or doc.personal_email,
            }
        )
        email_group.insert(ignore_permissions=True)


def remove_from_email_group(doc):
    """
    Remove the employee from the email group in ERPNext
    """
    groups = frappe.get_all("Email Group Member", filters={"email": doc.company_email})
    for group in groups:
        frappe.delete_doc("Email Group Member", group.name, ignore_permissions=True)


def add_to_user_permission(doc, method=None):
    """
    Add user permissions for the employee, based on the schools
    """
    if not doc.user_id:
        return

    # Get the school list
    if not doc.school:
        schools = frappe.get_all("School")
        for s in schools:
            add_user_permission(doc, s.name)
    else:
        # Remove existing user permissions if school is changed
        remove_user_permission(doc)  # Remove existing user permissions
        for s in doc.school:
            add_user_permission(doc, s.school)


def add_user_permission(doc, school):
    """
    add user permission for the employee to access the school
    """
    if frappe.db.exists("User Permission", {"user": doc.user_id, "allow": "School", "for_value": school}): return
    perm = frappe.new_doc("User Permission")
    perm.user = doc.user_id
    perm.allow = "School"
    perm.for_value = school
    perm.insert(ignore_permissions=True)


def remove_user_permission(doc, method=None):
    """
    Remove user permissions for the employee
    """
    user_permission = frappe.get_all("User Permission", filters={"user": doc.user_id, "allow": "School"})
    for up in user_permission:
        frappe.delete_doc("User Permission", up.name, ignore_permissions=True)


def get_google_group_info(doc, info_type="org_unit_path"):
    """
    Get the google group information based on the info_type
    """
    if not doc.branch:
        frappe.throw("Branch is mandatory to create a google user account")
    if not doc.role:
        frappe.throw("Role is mandatory to create a google user account")

    branch = frappe.get_doc("Branch", doc.branch)
    group = next((g for g in branch.google_groups if g.role == doc.role), None)
    return group.get(info_type, None) if group else None


def create_google_user_account(doc):
    """
    Create a google user account
    """
    org_unit_path = get_google_group_info(doc)
    org_unit_path = org_unit_path.strip() if org_unit_path else None
    email_key = doc.employee_name.lower().strip().replace(" ", ".")
    # Create a Google User
    company_email = create_employee_google_user(
        email_key,
        doc.first_name,
        doc.last_name,
        doc.personal_email,
        org_unit_path=org_unit_path,
    )
    doc.company_email = company_email
    doc.save()
    doc.reload()


def get_username(email):
    return email.split("@")[0]


def create_user(emp):
    employee_name = emp.employee_name.split(" ")
    middle_name = last_name = ""

    if len(employee_name) >= 3:
        last_name = " ".join(employee_name[2:])
        middle_name = employee_name[1]
    elif len(employee_name) == 2:
        last_name = employee_name[1]

    first_name = employee_name[0]

    email = emp.company_email or emp.personal_email
    username = get_username(email)

    user = frappe.new_doc("User")
    user.update(
        {
            "name": emp.employee_name,
            "email": email,
            "enabled": 1,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "gender": emp.gender,
            "birth_date": emp.date_of_birth,
            "phone": emp.cell_number,
            "bio": emp.bio,
            "username": username,
            "send_welcome_email": 0,
        }
    )
    user.append("roles", {"role": emp.role})
    user.insert()
    emp.user_id = user.name
    emp.save()
    emp.reload()


def create_employee_google_user(
    email_key, first_name, last_name, recovery_mail, org_unit_path=None
):
    user_service = get_google_admin_object()
    google_service_doc = frappe.get_single("Google Service Account")

    existing_user = None
    for i in range(4):
        existing_user = get_existing_google_user(email_key)
        if not existing_user:
            break
        email_key += str(i)

    company_email = f"{email_key}@{google_service_doc.domain}"

    if not existing_user:
        recovery_mail = (str(recovery_mail) or str(google_service_doc.default_recovery_mail)).strip().lower()
        email_pattern = r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        recovery_mail = (
            str(google_service_doc.default_recovery_mail)
            if not re.match(email_pattern, recovery_mail)
            else recovery_mail
        )

        new_user = {
            "primaryEmail": company_email,
            "name": {
                "givenName": first_name,
                "familyName": last_name,
            },
            "password": str(google_service_doc.default_password).strip(),
            "changePasswordAtNextLogin": True,
            "ipWhitelisted": False,
            "recoveryEmail": recovery_mail,
            "orgUnitPath": org_unit_path,
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
    domain = frappe.get_value("Google Service Account", None, "domain")
    user_key = f"{email_key}@{domain}".strip().lower()
    try:
        return (
            user_service.users()
            .get(
                userKey=user_key,
            )
            .execute()
        )
    except:
        return None


@frappe.whitelist()
def migrate_employee_data(employee, new_employee):
    """
    Migrate the employee data from one employee to another
    """
    try:
        employee = frappe.get_doc("Employee", employee)
        new_employee = frappe.get_doc("Employee", new_employee)
        employee.is_migrated = 1
        employee.save()
        # Transfer the teacher alias from the old employee to the new employee
        transfer_teacher_alias(employee, new_employee)
        # Transfer the CMAP data from the old employee to the new employee
        transfer_cmap_data(employee, new_employee)
        frappe.response["message"] = "Employee data migrated successfully"
    except:
        frappe.db.rollback()
        err_msg = "Error while migrating the employee data"
        frappe.log_error(err_msg,frappe.get_traceback(), reference_doctype="Employee", reference_name=employee.name)
        frappe.response["message"] = {
            "status": "error",
            "message": err_msg,
        }


@frappe.whitelist()
def mark_ex_employee(employee):
    """
    Mark the employee as an ex-employee
    """
    try:
        employee = frappe.get_doc("Employee", employee)
        employee.status = "Left"
        employee.relieving_date = frappe.utils.now()
        employee.save()

        # Suspend the google user
        if employee.company_email:
            email_key = employee.company_email.split("@")[0]
            google_user = get_google_user_with_key(email_key)
            if google_user:
                suspend_google_user(employee.company_email)
                # Send Mail to the exiting employee
                send_exiting_employee_mail(employee)

        # Mark the instructor as an ex-instructor if the employee is an instructor
        if frappe.db.exists("Instructor", {'employee': employee.name}):
            mark_ex_instructor(employee)
        frappe.response["message"] = "Employee marked as Ex-Employee"
    except:
        frappe.db.rollback()
        err_msg = "Error while marking the employee as Ex-Employee"
        frappe.log_error(err_msg,frappe.get_traceback(), reference_doctype="Employee", reference_name=employee.name)
        frappe.response["message"] = err_msg


def mark_ex_instructor(employee):
    """
    Mark the instructor as an ex-instructor
    """
    if not frappe.db.exists("Instructor", {'employee': employee.name}):
        frappe.throw("Instructor not found")
    frappe.db.set_value("Instructor", {'employee': employee.name}, "status", "Left")


def transfer_teacher_alias(old_employee, new_employee):
    """
    Transfers the teacher alias from an old employee to a new employee.

    Args:
        old_employee (str): The name of the old employee whose teacher alias is to be transferred.
        new_employee (str): The name of the new employee who will receive the teacher alias.
    """
    # Get the instructor documents for the old and new employees
    old_instructor = frappe.get_doc("Instructor", {'employee': old_employee.name})
    new_instructor = frappe.get_doc("Instructor", {'employee': new_employee.name})

    # Transfer the teacher aliases from the old employee to the new employee
    for alias in old_instructor.custom_teacher_alias:
        new_instructor.append("custom_teacher_alias", {"alias": alias.alias})
        frappe.delete_doc("Teacher Alias Group", alias.name)

    # Save the changes made to the new instructor document
    new_instructor.save()


def transfer_cmap_data(employee, new_employee):
    """
    Transfer the CMAP data from the old employee to the new employee

    Args:
        employee (Document): The name of the old employee whose CMAP data is to be transferred.
        new_employee (Document): The name of the new employee who will receive the CMAP data.
    """
    # Get the instructor documents for the old and new employees
    old_instructor = frappe.get_value("Instructor", {'employee': employee.name}, "name")
    new_instructor = frappe.get_value("Instructor", {'employee': new_employee.name}, "name")
    # Update the instructor field in the CMAP Assignment documents
    filters = {
        "teacher": old_instructor,
        "parenttype": "CMAP",
        "real_date": ["is", "not set"]
    }

    data = {
        "teacher": new_instructor,
    }

    frappe.db.set_value("CMAP Assignment", filters, data)


def send_exiting_employee_mail(employee):
    """
    Send the mail to the exiting employee, informing them about the account suspension
    """
    try:
        from nextai.funnel.custom_trigger import trigger_event
        trigger_event(employee, "employee_exited")
    except:
        frappe.log_error(
            f"Error while sending communication mail to the Ex-Employee",
            frappe.get_traceback(),
        )


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def employee_query(doctype, txt, searchfield, start, page_len, filters):
    school = filters.get('school')
    if not school:
        frappe.throw("Instructor or School is not present for the Employee")
    query = f"""
            SELECT
                emp.name, emp.employee_name
            FROM
                `tabEmployee` emp
            WHERE
                emp.status = 'Active'
                AND emp.name IN (
                    SELECT
                        instructor.employee
                    FROM
                        `tabInstructor` instructor
                    WHERE instructor.custom_school = '{school}'
                )
            AND emp.name LIKE %(txt)s OR emp.employee_name LIKE %(txt)s
            ORDER BY
                emp.name
        """
    return frappe.db.sql(query, {"txt": "%{}%".format(txt)})