import frappe
from frappe.utils import strip
import json
from edu_quality.public.py.utils import im_2_b64, gen_qr_code_b64
from weasyprint import CSS, HTML

# from pdf2image import convert_from_bytes
# import imgkit
# import base64


@frappe.whitelist()
def name(self):
    self = json.loads(self) if isinstance(self, str) else self

    if not self.get("item_group"):
        return

    current_item_group = frappe.get_doc("Item Group", self.get("item_group"))
    if current_item_group.get("parent_item_group") != "CMAP":
        return

    short_code = current_item_group.custom_group_code
    subject = frappe.get_doc("Course", self.get("custom_subject"))
    textbook = frappe.get_doc("Textbook", self.get("custom_textbook"))
    chapter = frappe.get_doc("Topic", self.get("custom_chapter"))
    syllabus = subject.get("custom_syllabus")
    language = subject.get("custom_language")
    class_name = self.get("custom_class")
    textbook_short_code = textbook.get("short_code")
    class_doc = frappe.get_doc("Class Type", class_name)
    syllabus_code = "C" if syllabus == "CBSE" else "S"
    language_short_code = "E" if language == "English" else "M"
    chapter_code = chapter.get("custom_chapter_number")
    sheet_number = self.get("custom_sheet_number")
    item_code = strip(
        f"{short_code}{language_short_code}{syllabus_code}{class_doc.short_code}{textbook_short_code}{str(chapter_code).zfill(2)}{str(sheet_number).zfill(2)}"
    )
    return item_code


def autoname(self, method=None):
    self.item_code = name(self)
    self.name = self.item_code
    self.item_name = self.item_code


@frappe.whitelist()
def calculate_sheet_number(self):
    self = json.loads(self) if isinstance(self, str) else self
    if not self.get("item_group"):
        return

    current_item_group = frappe.get_doc("Item Group", self.get("item_group"))
    if current_item_group.get("parent_item_group") != "CMAP":
        return

    sheet_number = 1
    list_topics = frappe.db.get_list(
        "Item",
        fields=["custom_sheet_number"],
        filters=[
            ["custom_is_cmap", "=", 1],
            ["item_group", "=", self.get("item_group")],
            ["custom_textbook", "=", self.get("custom_textbook")],
            ["custom_subject", "=", self.get("custom_subject")],
            ["custom_class", "=", self.get("custom_class")],
            ["custom_chapter", "=", self.get("custom_chapter")],
        ],
        limit=1,
        order_by="custom_sheet_number DESC",
        ignore_permissions=True,
    )
    frappe.errprint(list_topics)
    if list_topics and len(list_topics):
        sheet_number = list_topics[0].get("custom_sheet_number") + 1
    return sheet_number


def before_insert(self, method=None):
    self.custom_sheet_number = calculate_sheet_number(self)


@frappe.whitelist()
def get_qr_code(name):
    return gen_qr_code_b64(name)


def generate_worksheet_template(chapter_name, subject_name, qr_code, worksheet_name):
    base_url = frappe.utils.get_url()
    template = frappe.render_template(
        "edu_quality/templates/pdf/worksheet_header.html",
        {
            "chapter_name": chapter_name,
            "subject_name": subject_name,
            "qr_code": qr_code,
            "worksheet_name": worksheet_name,
        },
    )
    # test2 = imgkit.from_string(
    #     template,
    #     output_path=False,
    # )
    # frappe.errprint(render_template_to_image(template))
    # print(test2)
    # test = HTML(string=template)
    # test.write_png()
    # frappe.errprint(test)
    html = HTML(
        string=template,
        base_url=base_url,
    )
    main_doc = html.render()
    main_doc = main_doc.write_pdf()
    # frappe.errprint(main_doc)
    kitoptions = {
        "enable-local-file-access": None,
        # "width": 2480,
        # "height": 831,
        # "disable-smart-width": "",
    }
    # return template
    # image_bytes = imgkit.from_string(template, False, options=kitoptions)
    # image = base64.b64encode(image_bytes).decode("utf-8")
    # return f"data:image/png;base64,{image}"
    frappe.local.response.filename = "Temporary Id Card.pdf".format(
        name="Worksheet No.pdf".replace(" ", "-").replace("/", "-")
    )
    frappe.local.response.filecontent = main_doc
    frappe.local.response.type = "pdf"


@frappe.whitelist()
def get_worksheet_template(name):
    worksheet_doc = frappe.get_doc("Item", name)
    subject = worksheet_doc.get("custom_subject")
    chapter = worksheet_doc.get("custom_chapter")
    chapter_doc = frappe.get_doc("Topic", chapter)
    subject_doc = frappe.get_doc("Course", subject)

    qr_code = gen_qr_code_b64(name)
    return generate_worksheet_template(
        chapter_name=gen_chapter_name(chapter_doc),
        subject_name=gen_subject_name(worksheet_doc.custom_sheet_number, subject_doc),
        qr_code=qr_code,
        worksheet_name=name,
    )


def gen_chapter_name(chapter_doc):
    chapter_code = str(chapter_doc.get("custom_chapter_number", "")).zfill(2)
    str_without_name = f"{chapter_code}: TO_REPLACE - {chapter_code}"
    length_left = 38 - len(str_without_name)
    name_chapter = chapter_doc.topic_name.split("-")[1].strip()
    if len(name_chapter) <= length_left:
        new_string = str_without_name.replace("TO_REPLACE", name_chapter)
    else:
        new_string = str_without_name.replace(
            "TO_REPLACE", name_chapter[:: length_left - 3] + "..."
        )
    return new_string


def gen_subject_name(worksheet_id, subject_doc):
    subject = str(subject_doc.get("name", "")).zfill(2)
    str_without_name = f"{worksheet_id}: TO_REPLACE "
    length_left = 23 - len(str_without_name)
    if len(subject) <= length_left:
        new_string = str_without_name.replace("TO_REPLACE", subject)
    else:
        new_string = str_without_name.replace(
            "TO_REPLACE", subject[:: length_left - 3] + "..."
        )
    return new_string
