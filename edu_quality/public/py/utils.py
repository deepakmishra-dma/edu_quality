import frappe
import math, random
import requests
import urllib
import re
from io import BytesIO
import base64
import qrcode

try:
    from nextai.funnel.custom_trigger import trigger_event
except ImportError:
    print("Chatnext is not installed")


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
    from edu_quality.edu_quality.server_scripts.document_links import update_links
    update_links()
    set_property("Fees", "due_date", "reqd", "Check", 0)
    set_property("Fees", "fee_schedule", "reqd", "Check", 0)
    set_property("Fee Schedule", "due_date", "reqd", "Check", 0)
    set_property("Fee Schedule", "due_date", "hidden", "Check", 1)
    set_property("Program", "program_name", "unique", "Check", 0)
    set_property("Student Group", "student_group_name", "unique", "Check", 0)


@frappe.whitelist()
def trigger_funnel_event(doc, event_name):
    try:
        trigger_event(doc, event_name)
        return True
    except Exception as e:
        return False


def is_deposit(fees, term):
    deposit = False
    if fees.payment_schedule:
        for schedule in fees.payment_schedule:
            if (
                schedule.payment_term == term
                and "deposit" in schedule.description.lower()
            ):
                deposit = True
    return deposit


@frappe.whitelist()
def send_payment_link_email(doc, url, deposit=False):
    if deposit:
        template_name = frappe.get_single("Communications").deposit_email
    else:
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
        "link": url,
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
        for i in range(4):
            OTP += digits[math.floor(random.random() * 10)]
        rs.set_value(key, OTP, expires_in_sec=300)
        return send_otp(fee, OTP)
    except Exception as e:
        return False


def get_mobile_number(student):
    if student.student_mobile_number:
        return student.student_mobile_number
    elif student.primary_contact:
        return student.primary_contact
    elif student.whatsapp_number:
        return student.whatsapp_number
    elif student.day_care_contact:
        return student.day_care_contact
    else:
        return False


def get_email_id(student):
    if student.student_email_id:
        return student.student_email_id
    else:
        return False
    

def send_otp(fee, otp):
    try:
        student = frappe.get_value("Fees", fee, "student")
        student = frappe.get_doc("Student", student)
        email = get_email_id(student)
        mobile = get_mobile_number(student)
        if mobile:
            sms_otp(mobile, otp)
        if email:
            email_otp(email, otp)
        return True
    except Exception as e:
        return False


def email_otp(email, otp):
    subject = "OTP for Changing Payment Plan"
    message = f"OTP for Changing Payment Plan is {otp}"
    frappe.sendmail(recipients=email, subject=subject, message=message, delayed=False)


@frappe.whitelist(allow_guest=True)
def sms_otp(number, otp):
    api_key = "***REMOVED-SMS-KEY***"
    message = (
        f"{otp} is OTP for updating child details (JE08) initiated by you -Team Walnut"
    )
    template_id = 1007162244812510707
    sender = "WLTSCL"
    encoded_message = requests.utils.quote(message)
    url = f"http://smssolution.net.in/api/v4/?api_key={api_key}&method=sms&message={encoded_message}&to={number}&sender={sender}&template_id={template_id}"
    response = requests.post(url)
    response = response.json()
    return response


@frappe.whitelist()
def verify_otp(fee, otp):
    try:
        rs = frappe.cache()
        if rs.get_value(fee) == otp:
            return True
        return False
    except Exception as e:
        return False


def get_undertaking_template(doc=None, is_deposit=False, fee=None):
    if fee:
        doctype = "Fees"
        docname = fee
    else:
        doctype, docname = frappe.get_value(
            "Payment Request", doc.name, ["reference_doctype", "reference_name"]
        )
    if doctype == "Fee Advance":
        class_name, academic_year, student = frappe.get_value(
            doctype, docname, ["next_program", "academic_year", "student"]
        )
    else:
        class_name, academic_year, student = frappe.get_value(
            doctype, docname, ["program", "academic_year", "student"]
        )
    status = is_old_student(student, academic_year)
    filter_dict = {"class": class_name, "academic_year": academic_year}

    if is_deposit:
        filter_dict["show_on"] = "Deposit"
    else:
        filter_dict["show_on"] = "Fees"

    if status:
        filter_dict["status"] = "Current Student"
    else:
        filter_dict["status"] = "New Student"

    # check if doc filter exists in database
    template = frappe.db.get_value(
        "Rules and Regulation Template", filter_dict, ["pdf", "name"]
    )

    # change the filter to check for the show_on Both
    if not template:
        filter_dict["show_on"] = "Both"
        template = frappe.db.get_value(
            "Rules and Regulation Template", filter_dict, ["pdf", "name"]
        )

    # check if default filter exists in database
    if not template:
        default_filter = {
            "class": class_name,
            "academic_year": academic_year,
            "status": "Defaulter",
        }
        template = frappe.db.get_value(
            "Rules and Regulation Template", default_filter, ["pdf", "name"]
        )

    if template:
        site_url = frappe.utils.get_url()
        pdf_url = site_url + template[0]
        return pdf_url

    return None


def get_submitted_undertaking(payment_request):
    student = payment_request.party
    doctype = payment_request.reference_doctype
    docname = payment_request.reference_name
    if doctype == "Fees":
        class_name = frappe.get_value("Fees", docname, "program")
    elif doctype == "Fee Advance":
        class_name = frappe.get_value("Fee Advance", docname, "next_program")
    if frappe.db.exists(
        "Rules and Regulation Submission",
        {"student": student, "program": class_name},
        "name",
    ):
        # template = frappe.get_value("Rules and Regulation Submission", {"student": student}, 'rules_and_regulation_template')
        # academic_year = frappe.get_value("Rules and Regulation Template", template, 'academic_year')
        # current_academic_year = frappe.get_value("Academic Year", {"custom_current_academic_year": 1}, "name")
        # next_academic_year = frappe.get_value("Academic Year", {"custom_next_academic_year": 1}, "name")
        # return (doctype == "Fees" and academic_year == current_academic_year) or (doctype == "Fee Advance" and academic_year == next_academic_year)
        return True
    else:
        return False


@frappe.whitelist(allow_guest=True)
def handle_undertaking_submission(**kwargs):
    if kwargs.get("fee"):
        doc = frappe.get_doc("Fees", kwargs.get("fee"))
        student = doc.student
        doctype = "Fees"
        docname = doc.name
    else:
        payment_hash = kwargs.get("payment_request")
        student, doctype, docname = frappe.get_value(
            "Payment Request",
            {"payment_hash": payment_hash},
            ["party", "reference_doctype", "reference_name"],
        )
    if doctype == "Fees":
        class_name = frappe.get_value("Fees", docname, "program")
    elif doctype == "Fee Advance":
        class_name = frappe.get_value("Fee Advance", docname, "next_program")

    template = frappe.get_value(
        "Rules and Regulation Template", {"class": class_name}, "name"
    )
    student_doc = frappe.get_doc("Student", student)
    fathers_name = frappe.get_value(
        "Student Guardian", {"parent": student, "relation": "Father"}, "guardian_name"
    )
    mothers_name = frappe.get_value(
        "Student Guardian", {"parent": student, "relation": "Mother"}, "guardian_name"
    )

    if not frappe.db.exists(
        "Rules and Regulation Submission",
        {"student": student_doc.name,"program":class_name},
    ):
        new_doc = frappe.new_doc("Rules and Regulation Submission")
        new_doc.student = student_doc.name
        new_doc.reference_no = student_doc.reference_number
        new_doc.fathers_name = fathers_name
        new_doc.mothers_name = mothers_name
        new_doc.program = class_name
        new_doc.submitted_with_response = "Yes"
        new_doc.rules_and_regulation_template = template
        new_doc.submitted_date = frappe.utils.nowdate()
        new_doc.otp_entered = kwargs.get("otp")
        new_doc.otp_sent_to_contact_no = get_mobile_number(student_doc)
        new_doc.otp_sent_to_email_id = student_doc.student_email_id
        new_doc.ip_address = kwargs.get("ip_address")
        new_doc.user_info = kwargs.get("browser_info")
        new_doc.save(ignore_permissions=True)

        try:
            # trigger_event(new_doc, "rules_and_regulation_submission")
            return True
        except Exception as e:
            frappe.logger("edu_quality").exception(e)
            return False


def get_undertaking_submission_pdf(student):
    if frappe.db.exists("Rules and Regulation Submission", {"student": student}):
        name = frappe.get_value(
            "Rules and Regulation Submission", {"student": student}, "name"
        )
        return frappe.attach_print(
            "Rules and Regulation Submission", name, file_name=name
        )
    else:
        return None


def is_old_student(student, academic_year):
    previous_academic_year = get_previous_academic_year(academic_year)
    if frappe.db.exists(
        "Program Enrollment",
        {"student": student, "academic_year": previous_academic_year},
    ):
        return True
    else:
        return False


def get_previous_academic_year(academic_year):
    if not academic_year:
        return False

    start_year, end_year = map(int, academic_year.split("-"))
    previous_academic_year = f"{start_year - 1}-{end_year - 1}"

    return bool(
        frappe.get_value("Academic Year", {"name": previous_academic_year}, "name")
    )


# edu_quality.public.py.utils.generate_fields_map
@frappe.whitelist()
def generate_fields_map(docName="Lead"):
    meta = frappe.get_meta(docName)
    fields = meta.get("fields", None)
    if not fields:
        raise Exception(f"Error getting fields from {docName} Doctype")
    fields_dict = {}
    fields_array = []
    for i in fields:
        fields_dict[i.get("fieldname")] = True
        fields_array.append(i.get("fieldname"))
    return {"dict": fields_dict, "array": fields_array}


def convert_time_string_to_hours(time_string):
    if not time_string:
        return None
    hours, minutes, seconds_and_ms = time_string.split(":")
    seconds, milliseconds = seconds_and_ms.split(".")

    # Convert hours, minutes, seconds, and milliseconds to integers
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)

    # Calculate the total time in hours
    total_hours = hours + (minutes / 60) + (seconds / 3600) + (milliseconds / 3600000)
    return total_hours


def add_indian_country_code(number, add_plus=False):
    if not number:
        return ""
    try:
        phone_pattern = r"^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$"
        number = re.sub(r"\s", "", str(number))
        is_91 = re.findall(phone_pattern, str(number))[0][0]

        if is_91:
            return number
        else:
            if add_plus:
                return "+91"+number
            return "91" + number

    except Exception as e:
        frappe.log_error("Error adding indian country code", str(e))
        return number


def im_2_b64(image):
    """
    Converts image to base 64 jpeg
    """
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{img_str}"


def gen_qr_code_b64(str):
    frappe.errprint("hiya")
    return im_2_b64(qrcode.make(str))
