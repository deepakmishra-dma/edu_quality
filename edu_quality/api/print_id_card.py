import os
from frappe.utils.jinja import validate_template
from frappe.utils.weasyprint import download_pdf, get_html
import frappe
from weasyprint import CSS, HTML
import json
from PIL import Image
from pathlib import Path
from datetime import datetime


def divide_into_subarrays(arr, max_size):
    result = [arr[i : i + max_size] for i in range(0, len(arr), max_size)]
    return result


def hex_to_rgb(hex_color):
    if not hex_color:
        return (85, 62, 43)
    if hex_color[0] == "#":
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def get_image_path(image_path):
    image_path = str(image_path)
    site_path = frappe.get_site_path()
    if "private" in image_path:
        return Path(site_path + image_path)
    else:
        return Path(site_path + "/public" + image_path)


def change_image_bg(image_path, bg_color):
    fill_color = hex_to_rgb(bg_color)
    image_path = get_image_path(image_path)
    im = Image.open(image_path)
    original_mode = im.mode
    if original_mode in ("RGBA", "LA"):
        im = im.convert("RGBA")
        background = Image.new(im.mode[:-1], im.size, fill_color)
        background.paste(im, im.split()[-1])  # omit transparency
        im = background
    new_file_name = f"{image_path.stem}_bg_{bg_color.replace('#', '')}.jpg"
    dir_name = Path(frappe.get_site_path() + "/public/files/converted/")
    dir_name.mkdir(parents=True, exist_ok=True)
    new_image_path = dir_name / new_file_name
    im.convert("RGB" if original_mode in ("RGBA", "RGB", "LA") else original_mode).save(
        new_image_path, "JPEG"
    )
    new_image_path = new_image_path.relative_to(
        Path(frappe.get_site_path() + "/public")
    )
    return str(new_image_path)


def background_image(program_enrollment):
    bg_dict = {}
    for pe in program_enrollment:
        school = frappe.get_doc("School", pe.custom_school)
        division = frappe.get_doc("Student Group", pe.student_group)
        batch = frappe.get_doc("Student Batch Name", division.batch)
        image_path = change_image_bg(school.id_card_template, batch.batch_color)
        bg_dict[pe.name] = image_path
    return bg_dict


def get_division_name(program_enrollment):
    div_dict = {}
    for pe in program_enrollment:
        div = frappe.get_value("Student Group", pe.student_group, "student_group_name")
        class_name = frappe.get_value("Program", pe.program, "short_code")
        div_dict[pe.name] = (class_name or "") + div

    return div_dict


def get_batch_number(program_enrollment):
    div_dict = {}
    for pe in program_enrollment:
        div = frappe.get_doc("Student Group", pe.student_group)
        batch_number = frappe.get_value(
            "Student Batch Name", div.batch, "custom_batch_number"
        )
        div_dict[pe.name] = batch_number

    return div_dict


def house_color(program_enrollment):
    house_dict = {}
    for pe in program_enrollment:
        house_color = frappe.get_value("School House", pe.school_house, "house_color")
        house_dict[pe.name] = house_color or ""
    return house_dict


@frappe.whitelist()
def generate(**kwargs):
    print(kwargs)
    # kwargs["enrollments"] = json.loads(kwargs.get("enrollments", []))
    # letter_head = frappe.get_doc("letter_head")
    base_url = frappe.utils.get_url()

    program_enrollment = [
        frappe.get_doc("Program Enrollment", enrollment)
        for enrollment in kwargs.get("enrollments")
    ]

    enrollment_in_chunks = divide_into_subarrays(program_enrollment, 4)

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


@frappe.whitelist()
def generate_permanent_id_cards(enrollments):
    enrollments = json.loads(enrollments)
    program_enrollment = frappe.db.get_all(
        "Program Enrollment",
        filters=[["name", "in", enrollments]],
        fields=["custom_school", "name", "custom_status", "academic_year", "student"],
    )
    hash = None
    STATUSES = ["Cancelled", "Alumni"]
    for i in program_enrollment:
        student_status = frappe.get_value("Student", i.student, "student_status")
        name = i.get("name")
        if i.get("custom_status") in STATUSES or student_status in STATUSES:
            frappe.msgprint("ga")
            return frappe.throw(
                f"Cannot Create ID Card for cancelled student or alumni students {name}"
            )
        if not hash:
            hash = i
        elif hash.get("custom_school") != i.get("custom_school"):

            return frappe.throw(f"School is not same for all selected, in {name}")
        elif hash.get("academic_year") != i.get("academic_year"):

            return frappe.throw(
                f"Academic Year is not same for all selected, in {name}"
            )
    frappe.enqueue(
        generate_permanent_id_cards_async, enrollments=enrollments, queue="long"
    )
    return "Enqueued Successfully"


def generate_permanent_id_cards_async(**kwargs):
    try:
        base_url = frappe.utils.get_url()
        config = frappe.get_site_config()
        site_url = config.get("site_url")

        program_enrollment = [
            frappe.get_doc("Program Enrollment", enrollment)
            for enrollment in kwargs.get("enrollments")
        ]

        enrollment_in_chunks = divide_into_subarrays(program_enrollment, 5)
        background_images = background_image(program_enrollment)
        divisions = get_division_name(program_enrollment)
        batch_numbers = get_batch_number(program_enrollment)
        house_colors = house_color(program_enrollment)

        template = frappe.render_template(
            "edu_quality/templates/pdf/multiple_permanent_id_card.html",
            {
                "program_enrollments": enrollment_in_chunks,
                "background_images": background_images,
                "divisions": divisions,
                "house_colors": house_colors,
                "batch_numbers": batch_numbers,
                "site_url": site_url or "",
            },
        )
        html = HTML(string=template, base_url=base_url)
        main_doc = html.render()
        main_pdf = main_doc.write_pdf()

        public_path = Path(frappe.get_site_path(), "public")

        os.makedirs(public_path, exist_ok=True)

        current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"Permanent_Id_Card_{current_datetime}.pdf"
        filename = public_path / "files" / "converted" / filename

        with open(filename, "wb") as f:
            f.write(main_pdf)
        doc = frappe.new_doc("Permanent Id Card")
        file_path = str(filename).replace(str(public_path), "")

        for enrollment in program_enrollment:
            doc.append(
                "id_cards",
                {
                    "program_enrollment": enrollment.name,
                },
            )
            frappe.db.set_value(
                "Student ID Card",
                enrollment.custom_id_card,
                "status",
                "PENDING(PDF CREATED)",
            )

            frappe.get_doc(
                {
                    "doctype": "ID Card Event",
                    "parenttype": "Student ID Card",
                    "timestamp": frappe.utils.now(),
                    "parentfield": "events",
                    "status": "PENDING(PDF CREATED)",
                    "user": frappe.session.user,
                    "parent": enrollment.custom_id_card,
                }
            ).insert(ignore_permissions=True)
        doc.file = file_path
        doc.save(ignore_permissions=True)

    except Exception as e:
        frappe.logger("permanent_id_card").exception(e)
        frappe.log_error(
            "Permanent Id Card Generation Failed", str(frappe.get_traceback())
        )


@frappe.whitelist()
def send_id_card_mail(**kwargs):

    try:

        frappe.sendmail(
            subject=kwargs.get("subject"),
            recipients=kwargs.get("recipients"),
            bcc=kwargs.get("bcc"),
            content=kwargs.get("content"),
            attachments=kwargs.get("attachments"),
        )
    except Exception as e:
        frappe.log_error("Sending Id Card Mail", str(e))
        frappe.logger("sending purchase order").exception(e)
        raise e
