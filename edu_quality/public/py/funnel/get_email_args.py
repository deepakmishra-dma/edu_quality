import json
import frappe
from nextai.funnel.doctype.funnel_task import action_return_keys
from edu_quality.public.py.utils import is_deposit

# task data -> output from previous action or trigger
# action_node -> action node from funnel definition
def get_email_args(action_node, task_data):
    src_doc = task_data['doc']
    doctype = src_doc.get("doctype")
    docname = src_doc.get("name")

    # do your things -- start
    # get payment request doctyp
    context = get_arguments(doctype, docname)

    extra_email_args = {
        "attachments": [{
            "doctype": doctype,
            "name": docname,
            "print_format": "Standard",
        }],
        "delayed": False,
    }

    result_overrides = {
        "task": "email sent",
        "docname": src_doc.get("name"),
        "extra_email_args": extra_email_args,
        "context": context
    }
    
    # do your things -- end

    return {
        # result is to be used as inout of next action(s) in the chain
        action_return_keys.result: {  # or simply "result"
            **task_data,
            **result_overrides
        }
    }


def get_arguments(doctype, docname):
    if doctype == "Rules and Regulation Submission":
        undertaking_doc = frappe.get_doc(doctype, docname)
        student_doc = frappe.get_doc("Student", undertaking_doc.student)
        pdf = frappe.get_value("Rules and Regulation Template", undertaking_doc.rules_and_regulation_template, "pdf")

        site_url = frappe.utils.get_url()
        pdf_url = site_url + pdf

        context = {
            "refno": student_doc.custom_reference_number,
            "first_name": student_doc.first_name.capitalize(),
            "mother_name": student_doc.custom_mothers_first_name.capitalize(),
            "father_name": student_doc.custom_fathers_first_name.capitalize(),
            "submitted_with_response": undertaking_doc.submitted_with_response,
            "submitted_date": undertaking_doc.submitted_date,
            "otp_entered": undertaking_doc.otp_entered,
            "otp_sent_to_number": undertaking_doc.otp_sent_to_contact_no,
            "otp_sent_to_email": undertaking_doc.otp_sent_to_email_id,
            "ip_address": undertaking_doc.ip_address,
            "user_info": undertaking_doc.user_info,
            "link": pdf_url,
        }
        return context
    
    elif doctype == "Payment Request":
        doc = frappe.get_doc(doctype, docname)

        academic_year = frappe.db.get_value("Fees", doc.reference_name, "academic_year")
        first_name = frappe.db.get_value("Student", doc.party, "first_name")

        # Define variables to be used in Jinja templating
        context = {
            "first_name": first_name.capitalize(),
            "acad_year": academic_year,
            "link": doc.payment_url,
        }
        return context
    return {}