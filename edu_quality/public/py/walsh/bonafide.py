import frappe
from frappe.utils.file_manager import save_file
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


@frappe.whitelist(allow_guest=True)
def send_bonafide(student_id):
    try:
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
            student = frappe.get_doc("Student", student_id)

            frappe.set_user("Administrator")
            pdf_content = frappe.get_print(
                "Student", student_id, print_format="Bonafide Certificate", as_pdf=True
            )
            frappe.set_user(frappe.session.user)
            acad_year = current_academic_year()

            doc = frappe.get_doc(
                {
                    "doctype": "Bonafide Certificate",
                    "student": student_id,
                    "academic_year": acad_year,
                    "school": student.school,
                }
            )
            doc.insert(ignore_permissions=True)

            saved_file = save_file(
                fname=f"{student_id}.pdf",
                content=pdf_content,
                dt="Bonafide Certificate",
                dn=doc.name,
                df="bonafide_pdf",
            )
            if not doc.bonafide_pdf:
                doc.bonafide_pdf = saved_file.file_url
                doc.save()

            guardian_email = [i.guardian_name for i in student.guardians]
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
                attachments=[
                    frappe.attach_print(
                        "Student",
                        student_id,
                        print_format="Bonafide Certificate",
                        file_name=f"{student_id}",
                    )
                ],
            )
            pdf_url = frappe.utils.get_url(saved_file.file_url)
            return pdf_url
    except:
        frappe.log_error('Bonafide Certificate Sending Failed', frappe.get_traceback())