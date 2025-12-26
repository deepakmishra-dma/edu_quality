# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from PIL import Image
from autocrop import Cropper
import numpy as np
import io
from mimetypes import guess_type


def bgr_to_rbg(img):
    """Given a BGR (cv2) numpy array, returns a RBG (standard) array."""
    dimensions = len(img.shape)
    if dimensions == 2:
        return img
    return img[..., ::-1]


class StudentIDCard(Document):
    def autoname(self):
        student = frappe.get_value(
            "Program Enrollment", self.program_enrolled_in, "student"
        )
        academic_year = frappe.get_value(
            "Program Enrollment", self.program_enrolled_in, "academic_year"
        )
        name = make_autoname(student + "-{" + academic_year + "}-.###")
        self.name = name.replace("{", "(").replace("}", ")")

    def on_update(self):
        old_doc = self.get_doc_before_save()
        if old_doc and old_doc.status != self.status:
            frappe.get_doc(
                {
                    "doctype": "ID Card Event",
                    "timestamp": frappe.utils.now(),
                    "parenttype": "Student ID Card",
                    "parentfield": "events",
                    "status": self.status,
                    "user": frappe.session.user,
                    "parent": self.name,
                }
            ).insert(ignore_permissions=True)

    @property
    def photo_taken(self):
        return frappe.db.get_value(
            "Program Enrollment", self.program_enrolled_in, "image"
        )


# edu_quality.edu_quality.doctype.student_id_card.student_id_card.auto_crop
@frappe.whitelist()
def auto_crop():
    is_private = frappe.form_dict.is_private
    doctype = frappe.form_dict.doctype
    docname = frappe.form_dict.docname
    fieldname = frappe.form_dict.fieldname
    file_url = frappe.form_dict.file_url
    folder = frappe.form_dict.folder or "Home"
    filename = frappe.form_dict.file_name
    content = frappe.local.uploaded_file
    filename = frappe.local.uploaded_filename

    cropper = Cropper()
    image = Image.open(io.BytesIO(content))

    image_array = bgr_to_rbg(np.asarray(image))

    cropped_array = cropper.crop(image_array)

    if image.mode in ("RGBA", "LA") or (
        image.mode == "P" and "transparency" in image.info
    ):

        mode = "RGBA"
    else:

        mode = "RGB"

    content_type = guess_type(filename)[0]
    image_format = content_type.split("/")[1]

    enrollment = frappe.db.get_value("Student ID Card", docname, "program_enrolled_in")

    payload = {
        "doctype": "File",
        "attached_to_name": enrollment,
        "attached_to_doctype": "Program Enrollment",
        "attached_to_field": "image",
        "folder": folder,
        "file_name": f"{filename}",
        "file_url": file_url,
        "is_private": int(is_private),
    }

    try:
        payload["content"] = content
        non_cropped = frappe.get_doc(payload).save(ignore_permissions=True)

        if cropped_array.any():
            cropped_image = Image.fromarray(cropped_array, mode=mode)
            output = io.BytesIO()
            cropped_image.save(output, format=image_format, quality=100)
            optimized_content = output.getvalue()
            payload["content"] = optimized_content
            payload["file_name"] = f"cropped_{filename}"
            cropped_doc = frappe.get_doc(payload).save(ignore_permissions=True)

    except Exception as e:
        frappe.throw("Error Cropping Image, Try again")
    finally:
        doc = cropped_doc or non_cropped
        if doc.file_url:
            frappe.db.set_value("Program Enrollment", enrollment, "image", doc.file_url)


def schedule_upload_to_drive():
    pass
