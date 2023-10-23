import frappe
import math, random
import requests
import urllib

def set_property(doctype, fieldname, prop, property_type, value):
    filters = {
        "doctype_or_field": "DocField",
        "doc_type": doctype,
        "field_name": fieldname,
        "property": prop,
        "property_type": property_type,
        "value": value,
    }
    if not frappe.db.exists("Property Setter", filters):
        ps = frappe.new_doc("Property Setter")
        ps.module = "Edu Quality"
        ps.doctype_or_field = "DocField"
        ps.doc_type = doctype
        ps.field_name = fieldname
        ps.property = prop
        ps.property_type = property_type
        ps.value = value
        ps.insert(ignore_permissions=True)


def migrate():
    set_property("Fees", "due_date", "reqd", "Check", 0)
    set_property("Fees", "fee_schedule", "reqd", "Check", 0)
    set_property("Fee Schedule", "due_date", "reqd", "Check", 0)
    set_property("Fee Schedule", "due_date", "hidden", "Check", 1)
    set_property("Program", "program_name", "unique", "Check", 0)
    set_property("Student Group", "student_group_name", "unique", "Check", 0)


@frappe.whitelist()
def send_payment_link_email(doc, url):
    template_name = frappe.get_single("Communications").payment_link_email

    # Fetch the email template content from the doctype
    email_template = frappe.get_doc("Email Template", template_name)

    # Extract the subject and content from the email template
    subject = email_template.subject
    content = email_template.response

    academic_year = frappe.db.get_value("Fees", doc.reference_name, "academic_year")
    first_name = frappe.db.get_value("Student", doc.party, "first_name")
    email = frappe.db.get_value("Student", doc.party, "student_email_id")

    # Define variables to be used in Jinja templating
    context = {
        "first_name": first_name.capitalize(),
        "acad_year": academic_year,
        "fee_link": url,
    }

    # Render the Jinja template with the context
    content = frappe.render_template(content, context)
    pdf = [frappe.attach_print(doc.doctype, doc.name, file_name=doc.name)]
    # Create a dictionary with email parameters
    email_args = {
        "recipients": email,
        "subject": subject,
        "message": content,
        "attachments": pdf,
        "delayed": False,
    }

    # Send the email
    frappe.sendmail(**email_args)


def send_receipt_over_email(payment_request):
    payment_entries = frappe.get_list(
        "Payment Entry", {"reference_no": payment_request.name}
    )
    student = payment_request.party
    email = frappe.db.get_value("Student", student, "student_email_id")
    undertaking_submission_pdf = get_undertaking_submission_pdf(student)

    print_format, letter_head = get_print_format(payment_request.name)

    attachments = [
        frappe.attach_print(
            "Payment Entry",
            pe.name,
            file_name=pe.name,
            print_format=print_format,
            print_letterhead=True,
        )
        for pe in payment_entries
    ]

    if undertaking_submission_pdf:
        attachments.append(undertaking_submission_pdf)

    email_args = {
        "recipients": email,
        "subject": "Payment Receipt",
        "message": "Please find the attached payment receipt",
        "attachments": attachments,
        "delayed": False,
    }

    if attachments:
        frappe.sendmail(**email_args)


def get_print_format(payment_request):
    fee_name = frappe.db.get_value("Payment Request", payment_request, "reference_name")
    program_name = frappe.db.get_value("Fees", fee_name, "program")
    print_format = frappe.db.get_value("Program", program_name, "print_format")
    letter_head = frappe.db.get_value("Program", program_name, "letter_head")
    return print_format, letter_head


@frappe.whitelist()
def generate_otp(fee):
    try:
        rs = frappe.cache()
        key = fee
        digits = "0123456789"
        OTP = ""
        for i in range(4) :
            OTP += digits[math.floor(random.random() * 10)]
        rs.set_value(key, OTP, expires_in_sec=300)
        return send_otp(fee, OTP)
    except Exception as e:
        return False


def send_otp(fee,otp):
    try:
        student = frappe.get_value("Fees",fee,"student")
        student = frappe.get_doc("Student",student)
        if student.custom_fathers_email:
            email = student.custom_fathers_email
        elif student.custom_mothers_email:
            email = student.custom_mothers_email
        elif student.custom_guardians_email_id:
            email = student.custom_guardians_email_id
        if student.custom_fathers_mobile_no:
            mobile = student.custom_fathers_mobile_no
        elif student.custom_mothers_mobile_no:
            mobile = student.custom_mothers_mobile_no
        elif student.custom_guardians_mobile_no:
            mobile = student.custom_guardians_mobile_no
        if mobile:
            sms_otp(mobile,otp)
        if email:
            email_otp(email,otp)
        #whatsapp message
        return True
    except Exception as e:
        return False
    
def email_otp(email,otp):
    subject = "OTP for Changing Payment Plan"
    message = f"OTP for Changing Payment Plan is {otp}"
    frappe.sendmail(
        recipients=email, subject=subject, message=message, delayed=False
    )

@frappe.whitelist(allow_guest=True)
def sms_otp(number,otp):
    api_key = "***REMOVED-SMS-KEY***"
    url = "https://smssolution.net.in/api/v4/?api_key=" + api_key
    url += "&method=sms&message="
    message = "The%20OTP%20for%20making%20changes%20to%20your%20account%20is%20-%20" + str(otp)
    url += message
    url += "&to=" + number
    url += "&sender=" + "WALNUT"
    response = requests.post(url)
    response = response.json()
    return response




def verify_otp(fee,otp):
    try:
        rs = frappe.cache()
        if rs.get_value(fee) == otp:
            return True 
        return False
    except Exception as e:
        return False


def get_undertaking_template(doc, is_deposit=False):
    fee = frappe.get_value("Payment Request", doc.name, "reference_name")
    class_name, academic_year, student = frappe.get_value("Fees", fee, ["program", "academic_year", "student"])
    status = is_old_student(student, academic_year)
    filter_dict = {"class": class_name, "academic_year": academic_year}

    if is_deposit:
        filter_dict["show_on"] = "Deposit"
    else:
        filter_dict["show_on"] = "Fees"

    if status:
        filter_dict["status"] = "Rollover Student"
    else:
        filter_dict["status"] = "New Student"

    # check if doc filter exists in database
    template = frappe.db.get_value("Rules and Regulation Template", filter_dict, ["pdf", "name"])
    if template:
        site_url = frappe.utils.get_url()
        pdf_url = site_url + template[0]
        return pdf_url

    # check if default filter exists in database
    default_filter = {"class": class_name, "academic_year": academic_year, "status": "Defaulter"}
    template = frappe.db.get_value("Rules and Regulation Template", default_filter, ["pdf", "name"])
    if template:
        site_url = frappe.utils.get_url()
        pdf_url = site_url + template[0]
        return pdf_url

    return None
    
def get_submitted_undertaking(payment_request):
    student = frappe.get_value("Payment Request", payment_request, ["party"])

    if frappe.db.exists("Rules and Regulation Submission", {"student": student}):
        return True
    else:
        return False


@frappe.whitelist(allow_guest=True)
def handle_undertaking_submission(**kwargs):
    payment_hash = kwargs.get("payment_request")
    student, fee = frappe.get_value("Payment Request", {"payment_hash": payment_hash}, ["party", "reference_name"])
    class_name = frappe.get_value("Fees", fee, "program")
    template = frappe.get_doc("Rules and Regulation Template", {"class": class_name})
    student_doc = frappe.get_doc("Student", student)

    if not frappe.db.exists("Rules and Regulation Submission", {"reference_no": student_doc.custom_reference_number}):
        new_doc = frappe.new_doc("Rules and Regulation Submission")
        new_doc.student = student_doc
        new_doc.reference_no = student_doc.custom_reference_number
        new_doc.fathers_name = student_doc.custom_fathers_first_name
        new_doc.mothers_name = student_doc.custom_mothers_first_name
        new_doc.submitted_with_response = "Yes"
        new_doc.rules_and_regulation_template = template
        new_doc.submitted_date = frappe.utils.nowdate()
        new_doc.otp_entered = kwargs.get("otp")
        new_doc.otp_sent_to_contact_no = student_doc.custom_fathers_mobile_no
        new_doc.otp_sent_to_email_id = student_doc.student_email_id
        new_doc.ip_address = kwargs.get("ip_address")
        new_doc.user_info = kwargs.get("browser_info")
        new_doc.save(ignore_permissions=True)


def get_undertaking_submission_pdf(student):
    if frappe.db.exists("Rules and Regulation Submission", {"student": student}):
        name = frappe.get_value("Rules and Regulation Submission", {"student": student}, "name")
        return frappe.attach_print("Rules and Regulation Submission", name, file_name=name)
    else:
        return None
    

def is_old_student(student, academic_year):
    previous_academic_year = get_previous_academic_year(academic_year)
    if frappe.db.exists("Program Enrollment",{"student":student,"academic_year":previous_academic_year}):
        return True
    else:
        return False
    

def get_previous_academic_year(academic_year):
    # Extract the year parts from the current academic year
    current_year_parts = academic_year.split("-")
    current_start_year = int(current_year_parts[0])
    current_end_year = int(current_year_parts[1])

    # Calculate the start year of the previous academic year
    previous_start_year = current_start_year - 1
    previous_end_year = current_end_year - 1

    # Construct the previous academic year name
    previous_academic_year_name = f"{previous_start_year}-{previous_end_year}"

    # Check if the previous academic year exists
    previous_academic_year_exists = frappe.get_value("Academic Year", {"name": previous_academic_year_name}, "name")
    return bool(previous_academic_year_exists)