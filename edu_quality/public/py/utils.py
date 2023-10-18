import frappe
import math, random

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
def generate_otp(fee, mobile=None, email=None):
    try:
        rs = frappe.cache()
        key = fee
        digits = "0123456789"
        OTP = ""
        for i in range(4) :
            OTP += digits[math.floor(random.random() * 10)]
        rs.set_value(key, OTP, expires_in_sec=300)
        return send_otp(OTP, mobile, email)
    except Exception as e:
        return False

@frappe.whitelist()
def generate_undertaking_otp(payment_hash):
    fee = get_fee(payment_hash)
    mobile, email = get_contacts(fee)
    return generate_otp(fee, mobile, email)


@frappe.whitelist()
def verify_undertaking_otp(payment_hash, otp):
    fee = get_fee(payment_hash)
    return verify_otp(fee, otp)


def get_contacts(fee):
    student = frappe.get_value("Fees", fee, "student")
    mobile = frappe.get_value("Student", student, "custom_fathers_mobile_no")
    email = frappe.get_value("Student", student, "student_email_id")
    return mobile, email

def get_fee(payment_hash):
    fee = frappe.get_value("Payment Request", {"payment_hash": payment_hash}, "reference_name")
    return fee

    
def send_otp(otp, mobile=None, email=None):
    try:
        # OTP via email
        subject = "OTP for undertaking submission"
        message = f"OTP for undertaking submission is {otp}"
        frappe.sendmail(
            recipients=email, subject=subject, message=message, delayed=False
        )
        # whatsapp message
        return True
    except Exception as e:
        return False

@frappe.whitelist()
def verify_otp(fee, otp):
    try:
        rs = frappe.cache()
        if rs.get_value(fee) == otp:
            return True 
        return False
    except Exception as e:
        return False

def get_undertaking_template(doc):
    fee = frappe.get_value("Payment Request", doc.name, "reference_name")
    class_name, academic_year = frappe.get_value("Fees", fee, ["program", "academic_year"])
    doc_filter = {"class": class_name, "academic_year": academic_year}
    if frappe.db.exists("Rules and Regulation Template", doc_filter):
        template = frappe.get_doc("Rules and Regulation Template", doc_filter)
        site_url = frappe.utils.get_url()
        pdf_url = site_url + template.pdf
        return pdf_url
    else:
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