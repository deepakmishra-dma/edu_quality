from frappe.utils.jinja import validate_template
from frappe.utils.weasyprint import download_pdf, get_html
import frappe


def divide_into_subarrays(arr, max_size):
    result = [arr[i : i + max_size] for i in range(0, len(arr), max_size)]
    return result


@frappe.whitelist(allow_guest=True)
def generate(**kwargs):
    print(kwargs)
    from weasyprint import CSS, HTML

    # letter_head = frappe.get_doc("letter_head")
    base_url = frappe.utils.get_url()

    program_enrollment = [
        frappe.get_doc("Program Enrollment", enrollment)
        for enrollment in kwargs.get("enrollments")
    ]

    enrollment_in_chunks = divide_into_subarrays(program_enrollment, 8)

    template = frappe.render_template(
        "edu_quality/templates/pdf/multiple_temporary_id_card.html",
        {"program_enrollments": enrollment_in_chunks},
    )
    html = HTML(string=template, base_url=base_url)
    main_doc = html.render()
    main_pdf = main_doc.write_pdf()

    frappe.local.response.filename = "Temporary Id Card.pdf".format(
        name="Temporary Id Card.pdf".replace(" ", "-").replace("/", "-")
    )
    frappe.local.response.filecontent = main_pdf
    frappe.local.response.type = "pdf"
