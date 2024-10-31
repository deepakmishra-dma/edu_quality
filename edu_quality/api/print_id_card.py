import os
from frappe.utils.jinja import validate_template
from frappe.utils.weasyprint import download_pdf, get_html
import frappe
from weasyprint import CSS, HTML
import json
from PIL import Image
from pathlib import Path


def divide_into_subarrays(arr, max_size):
    result = [arr[i : i + max_size] for i in range(0, len(arr), max_size)]
    return result


def hex_to_rgb(hex_color):
    if not hex_color:
        return (85, 62, 43)
    if hex_color[0] == "#":
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def change_image_bg(image_path, bg_color):
    fill_color = hex_to_rgb(bg_color)
    image_path = Path(frappe.get_site_path() + str(image_path))
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
        div_dict[pe.name] = class_name + div
        
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
def generate_permanent_id_cards(**kwargs):
    base_url = frappe.utils.get_url()

    program_enrollment = [
        frappe.get_doc("Program Enrollment", enrollment)
        for enrollment in kwargs.get("enrollments")
    ]

    enrollment_in_chunks = divide_into_subarrays(program_enrollment, 5)
    background_images = background_image(program_enrollment)
    divisions = get_division_name(program_enrollment)
    house_colors = house_color(program_enrollment)

    template = frappe.render_template(
        "edu_quality/templates/pdf/multiple_permanent_id_card.html",
        {
            "program_enrollments": enrollment_in_chunks,
            "background_images": background_images,
            "divisions": divisions,
            "house_colors": house_colors,
        },
    )
    html = HTML(string=template, base_url=base_url)
    main_doc = html.render()
    main_pdf = main_doc.write_pdf()

    frappe.local.response.filename = "Permanent Id Card.pdf".format(
        name="Permanent Id Card.pdf".replace(" ", "-").replace("/", "-")
    )
    frappe.local.response.filecontent = main_pdf
    frappe.local.response.type = "pdf"
