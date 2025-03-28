import frappe
from frappe.utils.file_manager import save_file
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


@frappe.whitelist(allow_guest=True)
def send_bonafide(student_id):
    if frappe.db.exists(
        "Bonafide Certificate",
        {"student": student_id, "academic_year": current_academic_year()},
    ):
        bonafide_pdf = frappe.get_doc(
            "Bonafide Certificate", {"student": student_id}
        ).bonafide_pdf
        pdf_url = frappe.utils.get_url(bonafide_pdf)
        return pdf_url
    else:
        pdf_content = frappe.get_print(
            "Student", student_id, print_format="Bonafide Certificate"
        )
        acad_year = current_academic_year()

        doc = frappe.get_doc(
            {
                "doctype": "Bonafide Certificate",
                "student": student_id,
                "academic_year": acad_year,
            }
        )
        doc.insert()

        saved_file = save_file(
            fname=f"{student_id}.pdf",
            content=pdf_content,
            dt="Bonafide Certificate",
            dn=doc.name,
            df="bonafide_pdf",
            folder="bonafide_certificates"
        )

        guardians = frappe.get_value("Student", student_id, "guardians")

        guardian_email = [i.guardian_name for i in guardians]
        guardian = frappe.get_all(
            doctype="Guardian",
            fields=["email_address"],
            filters=[["guardian_name", "in", guardian_email]],
        )
        recipients = [i.email_address for i in guardian]

        frappe.sendmail(
            recipients=recipients,
            subject="Bonafide Certificate",
            message="Please find attached Bonafide Certificate",
            attachments=[saved_file.file_url],
        )
        pdf_url = frappe.utils.get_url(saved_file.file_url)
        return pdf_url
