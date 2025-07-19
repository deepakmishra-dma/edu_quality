import frappe
from frappe.auth import LoginManager
from frappe.utils.file_manager import save_file
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


@frappe.whitelist(allow_guest=True)
def send_bonafide(student_id):
    try:
        ay = current_academic_year()
        if frappe.db.exists(
            "Bonafide Certificate",
            {"student_name": student_id, "academic_year": ay},
        ):
            doc = frappe.get_doc(
                "Bonafide Certificate",
                {"student_name": student_id, "academic_year": ay},
            )
            bonafide_pdf = save_bonafide_pdf(student_id, doc.name)
            if not doc.bonafide_pdf:
                doc.bonafide_pdf = bonafide_pdf
                doc.save()

            pdf_url = frappe.utils.get_url(bonafide_pdf)
            return pdf_url
        else:
            student = frappe.get_doc("Student", student_id)
            acad_year = current_academic_year()

            doc = frappe.get_doc(
                {
                    "doctype": "Bonafide Certificate",
                    "academic_year": acad_year,
                    "student_name": student.name,
                    "school": student.school,
                    "reference_number": student.name,
                }
            )
            doc.insert(ignore_permissions=True)

            bonafide_pdf = save_bonafide_pdf(student_id, doc.name)
            if not doc.bonafide_pdf:
                doc.bonafide_pdf = bonafide_pdf
                doc.save()

            guardian_email = [i.guardian_name for i in student.guardians]
            guardian = frappe.get_all(
                doctype="Guardian",
                fields=["email_address"],
                filters=[["guardian_name", "in", guardian_email]],
            )
            recipients = [i.email_address for i in guardian]
            school_details = frappe.get_doc("School", student.school)
            bcc_admin = school_details.get("bcc_email_address")
            frappe.sendmail(
                recipients=recipients,
                bcc=[bcc_admin],
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
            pdf_url = frappe.utils.get_url(bonafide_pdf)
            return pdf_url
    except:
        frappe.log_error("Bonafide Certificate Sending Failed", frappe.get_traceback())


def get_pdf_content(student_id):
    current_user = frappe.session.user
    login_manager = LoginManager()
    login_manager.login_as("Administrator")
    pdf_content = frappe.get_print(
        "Student", student_id, print_format="Bonafide Certificate", as_pdf=True
    )
    login_manager.login_as(current_user)
    return pdf_content


def save_bonafide_pdf(student_id, bonafide_name):
    pdf_content = get_pdf_content(student_id)
    saved_file = save_file(
        fname=f"{student_id}.pdf",
        content=pdf_content,
        dt="Bonafide Certificate",
        dn=bonafide_name,
        df="bonafide_pdf",
    )
    return saved_file.file_url


@frappe.whitelist()
def bonafide_list(student_id):
    bonafide_doc = frappe.get_all(
        "Bonafide Certificate", filters={"student_name": student_id}, fields=["*"]
    )
    return bonafide_doc
