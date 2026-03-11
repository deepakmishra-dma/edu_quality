import base64
import random
import re
from io import BytesIO

import frappe
import qrcode
import requests
from typing import Union
from PIL import Image


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
def generate_otp(fee, undertaking=0):
    try:
        rs = frappe.cache()
        key = fee
        OTP = ""
        for i in range(4):
            OTP += str(random.randint(1, 9))
        rs.set_value(key, OTP, expires_in_sec=600)
        return send_otp(fee, OTP, undertaking)
    except Exception as e:
        frappe.logger("otp").exception(e)


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


def send_otp(fee, otp, undertaking):
    try:
        doctype = "Fee Advance"
        if frappe.db.exists("Fees", fee):
            doctype = "Fees"
        student = frappe.get_value(doctype, fee, "student")
        student = frappe.get_doc("Student", student)
        email = get_email_id(student)
        mobile = get_mobile_number(student)
        cc_email = parents_email(student.name)
        if mobile:
            sms_otp(mobile, otp)
        if email:
            email_otp(email, otp, undertaking, cc_email)
        return True
    except Exception as e:
        return False


def parents_email(student):
    recipients = []
    parent_emails = frappe.db.get_all(
        "Student Guardian",
        filters={"parent": student},
        fields=["guardian.email_address"],
        as_list=True,
    )
    parent_emails = [email[0] for email in parent_emails if email and email[0]]
    recipients.extend(parent_emails)
    return recipients


def email_otp(email, otp, undertaking, cc_email=None):
    try:
        if not undertaking:
            subject = "OTP for Changing Payment Plan"
            message = f"OTP for Changing Payment Plan is {otp}"
            frappe.sendmail(
                recipients=email,
                subject=subject,
                message=message,
                delayed=False,
                now=True,
            )
            return
        template = frappe.get_doc("Email Template", "Walnut - Undertaking OTP")
        context = dict(otp=otp)
        frappe.sendmail(
            cc=cc_email,
            recipients=email,
            subject=frappe.render_template(template.subject, context=context),
            message=frappe.render_template(template.response, context=context),
            delayed=False,
            now=True,
        )
    except Exception as e:
        frappe.logger("email_otp").exception(e)


@frappe.whitelist(allow_guest=True)
def sms_otp(number, otp):
    api_key = "***REMOVED-SMS-KEY***"
    message = f"{otp} is OTP for updating child details initiated by you -Team Walnut"
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
        frappe.logger("OTP").exception(e)
        return False


def get_undertaking_template(doc=None, is_deposit=False, fee=None):
    if fee:
        doctype = fee.doctype
        docname = fee.name
    else:
        doctype, docname = frappe.get_value(
            "Payment Request", doc.name, ["reference_doctype", "reference_name"]
        )
    if doctype == "Fee Advance":
        class_name, academic_year, student, school = frappe.get_value(
            doctype, docname, ["next_program", "academic_year", "student", "school"]
        )
    else:
        class_name, academic_year, student, school = frappe.get_value(
            doctype, docname, ["program", "academic_year", "student", "custom_school"]
        )
    if not frappe.get_value(
        "School", school, "custom_require_otp_for_accepting_rules_and_regulations"
    ):
        return None
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
    payment_term = payment_request.payment_term
    if doctype == "Fees":
        class_name, school = frappe.get_value(
            "Fees", docname, ["program", "custom_school"]
        )
    elif doctype == "Fee Advance":
        class_name, school = frappe.get_value(
            "Fee Advance", docname, ["next_program", "school"]
        )
    if frappe.get_value(
        "School",
        school,
        "custom_otp_for_every_installment_showing_rules_and_regulations",
    ):
        if frappe.db.exists(
            "Rules and Regulation Submission",
            {"student": student, "program": class_name, "payment_term": payment_term},
            "name",
        ):
            return True
        else:
            return False
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
        payment_term = kwargs.get("payment_term")
    elif kwargs.get("fee_advance"):
        doc = frappe.get_doc("Fee Advance", kwargs.get("fee_advance"))
        student = doc.student
        doctype = "Fee Advance"
        docname = doc.name
        payment_term = kwargs.get("payment_term")
    else:
        payment_hash = kwargs.get("payment_request")
        student, doctype, docname, payment_term = frappe.get_value(
            "Payment Request",
            {"payment_hash": payment_hash},
            ["party", "reference_doctype", "reference_name", "payment_term"],
        )
    if doctype == "Fees":
        class_name, school = frappe.get_value(
            "Fees", docname, ["program", "custom_school"]
        )
    elif doctype == "Fee Advance":
        class_name, school = frappe.get_value(
            "Fee Advance", docname, ["next_program", "school"]
        )

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
    if frappe.get_value(
        "School",
        school,
        "custom_otp_for_every_installment_showing_rules_and_regulations",
    ):
        if not frappe.db.exists(
            "Rules and Regulation Submission",
            {
                "student": student_doc.name,
                "program": class_name,
                "payment_term": payment_term,
            },
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
            new_doc.payment_term = payment_term
            new_doc.save(ignore_permissions=True)
    else:
        if not frappe.db.exists(
            "Rules and Regulation Submission",
            {"student": student_doc.name, "program": class_name},
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
    if previous_academic_year:
        if frappe.db.exists(
            "Program Enrollment",
            {"student": student, "academic_year": previous_academic_year},
        ):
            return True
        else:
            return False
    else:
        return False


def get_previous_academic_year(academic_year):
    if not academic_year:
        return False

    start_year, end_year = map(int, academic_year.split("-"))
    previous_academic_year = f"{start_year - 1}-{end_year - 1}"
    return frappe.get_value("Academic Year", {"name": previous_academic_year}, "name")


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
                return "+91" + number
            return "91" + number

    except Exception as e:
        frappe.log_error("Error adding indian country code", str(e))
        return number


def im_2_b64(image: Image) -> str:
    """
    Converts image to base 64 jpeg
    """
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{img_str}"


def im_2_b64_png(image):
    """
    Converts image to base 64 jpeg
    """
    buff = BytesIO()
    image.save(buff, format="PNG")
    img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"


def gen_qr_code_b64(input_str: Union[str, bytes]) -> str:

    return im_2_b64(qrcode.make(input_str))


def gen_qr_code_b64_transparent(str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,
    )
    qr.add_data(str)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="transparent")
    return im_2_b64_png(qr_img)


def to_snake_case(input_string=""):
    print(input_string)
    input_string = input_string.replace(" ", "_")

    input_string = input_string.lower()

    return input_string


def remove_indian_country_code(number):
    if not number:
        return ""
    try:
        phone_pattern = r"^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$"
        number = re.sub(r"\s", "", str(number))
        re_groups = re.findall(phone_pattern, str(number))

        if len(re_groups) == 0:
            return str(number)

        is_91 = re_groups[0][0]

        if is_91 == "+91" or is_91 == "91" or is_91 == "+910" or is_91 == "910":
            return str("".join(re_groups[0][1::]))
        else:
            return str(number)

    except Exception as e:
        frappe.log_error("Error adding indian country code on number " + number, str(e))
        return str(number)


@frappe.whitelist()
def email_recipients(variables, student, case):
    # case 0: only student
    # case 1: only parent
    # case 3: both
    recipients = []

    if case == 0 or case == 3:
        student_email = frappe.db.get_value("Student", student, "student_email_id")
        if student_email:
            recipients.append(student_email)

    if case == 1 or case == 3:
        parent_emails = frappe.get_all(
            "Student Guardian",
            filters={"parent": student},
            fields=["guardian.email_address"],
            as_list=True,
        )
        parent_emails = [email[0] for email in parent_emails if email and email[0]]
        recipients.extend(parent_emails)

    recipients_str = ", ".join(recipients)
    variables["recipients_str"] = recipients_str


def reduce_font_size_steps(initial_size, step, data, initial_char_length, lowest):
    if isinstance(data, str):
        txt = data
    elif isinstance(data, frappe.model.document.Document):
        txt = (
            (data.first_name or "")
            if len(data.first_name or "") > len(data.last_name or "")
            else (data.last_name or "")
        )
    if len(txt) <= initial_char_length:
        return initial_size
    rem = len(txt) % int(initial_char_length)
    res = int(initial_size) - int(rem) * float(step)
    if res < lowest:
        return str(lowest)

    return str(int(res))


def check_admin_roles(roles, additional_roles=None):
    roles_to_check = ["Administrator", "Walnut Admin", "System Manager"]
    if isinstance(additional_roles, list):
        roles_to_check += additional_roles

    for role in roles_to_check:
        if role in roles:
            return True
    return False


def check_roles(roles, roles_to_check):
    if isinstance(roles_to_check, list):
        roles_to_check += roles_to_check

    for role in roles_to_check:
        if role in roles:
            return True
    return False


def extract_year_from_academic_year_name(year: str):
    # assuming 2024-2025
    years = year.strip().split("-")
    short_forms = [str(year[-2:]) for year in years]
    return "-".join(short_forms)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def academic_year_query(doctype, txt, searchfield, start, page_len, filters):
    acad_year_qb = frappe.qb.DocType("Academic Year")
    return (
        frappe.qb.from_(acad_year_qb)
        .where(
            (acad_year_qb.custom_current_academic_year == 1)
            | (acad_year_qb.custom_next_academic_year == 1)
        )
        .select("name")
    ).run()


def render_template_with_exception(template, data):
    patch_logger = frappe.logger("Create ID Card Div")
    try:
        return frappe.render_template(template, data)
    except Exception as e:
        frappe.log_error("Error rendering template for data", frappe.get_traceback())
        frappe.logger("Error Rendering Template").exception(e)

        patch_logger.info(
            f"Failed rendering id card for data {data}",
        )
        return ""


def get_div_students(division, ref_no=None):
    if isinstance(division, list):
        cond = ["in", division]
    else:
        cond = division

    if ref_no:
        filters = {
            "student_group": cond,
            "docstatus": 1,
            "student": ref_no,
            "custom_status": ["in", ["Current student", "Defaulter"]],
        }

    else:
        filters = {
            "student_group": cond,
            "docstatus": 1,
            "custom_status": ["in", ["Current student", "Defaulter"]],
        }

    data = frappe.db.get_list(
        "Program Enrollment",
        filters=filters,
        fields=["student_name", "name", "student", "roll_no", "student_group"],
        order_by="CAST(roll_no AS UNSIGNED)",
    )

    return data


def get_descriptive_result(assessment_group, student):
    assess_plan_qb = frappe.qb.DocType("Assessment Plan")
    assess_res_qb = frappe.qb.DocType("Assessment Result")
    assess_res_de_qb = frappe.qb.DocType("Assessment Result Detail")
    assess_ques_res_qb = frappe.qb.DocType("Descriptive Question")
    query = (
        (
            frappe.qb.from_(assess_res_qb)
            .where(
                (assess_res_qb.docstatus == 1)
                & (assessment_group == assess_res_qb.assessment_group)
                & (assess_res_qb.student == student)
            )
            .inner_join(assess_plan_qb)
            .on(assess_plan_qb.name == assess_res_qb.assessment_plan)
            .inner_join(assess_res_de_qb)
            .on(assess_res_qb.name == assess_res_de_qb.parent)
            .inner_join(assess_ques_res_qb)
            .on(assess_res_de_qb.custom_question == assess_ques_res_qb.name)
        )
        .orderby(assess_plan_qb.custom_order, assess_res_de_qb.custom_order)
        .select(
            assess_res_de_qb.name.as_("criteria_name"),
            assess_res_qb.name,
            assess_res_qb.course,
            assess_res_de_qb.custom_question,
            assess_ques_res_qb.question.as_("question_name"),
            assess_res_de_qb.custom_parent_question,
            assess_res_de_qb.grade,
            assess_res_de_qb.custom_processed_grade,
            assess_res_qb.custom_processed_grade.as_("total_processed_grade"),
            assess_res_qb.custom_total_processed_score,
            assess_res_de_qb.custom_processed_result,
        )
    )

    data = query.run(as_dict=True)
    return split_desc_hash(generate_child_questions_hash(data))


def split_desc_hash(data):
    subject_question = {}
    for result_key in data:
        if not len(data[result_key]):
            continue

        subject = data[result_key][0].get("course")
        if not subject in subject_question:
            subject_question[subject] = data[result_key]
        else:
            subject_question[subject].extend(data[result_key])
    return subject_question


def generate_child_questions_hash(data):
    assessments_result_hash = {}
    final_result = {}
    for result in data:
        if result.name not in assessments_result_hash:
            assessments_result_hash[result.name] = [result]
        else:
            assessments_result_hash[result.name].append(result)

    for subject_wise_result in assessments_result_hash:
        tree_data = build_tree_iteratively(assessments_result_hash[subject_wise_result])
        final_result[subject_wise_result] = tree_data

    return final_result


def build_tree_iteratively(nodes):
    node_dict = {node["custom_question"]: node for node in nodes}
    tree = []
    for node in nodes:
        parent_question = node["custom_parent_question"]
        if parent_question == None:
            tree.append(node)
        else:
            parent_node = node_dict.get(parent_question)
            if parent_node:
                if "children" not in parent_node:
                    parent_node["children"] = []
                parent_node["children"].append(node)
                parent_node["children_length"] = len(parent_node["children"])
    return tree
