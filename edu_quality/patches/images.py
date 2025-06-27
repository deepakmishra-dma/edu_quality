import frappe


def execute():
    files = frappe.get_all(
        "File",
        filters=[
            ["folder", "!=", "Home/ID Cards To Sync"],
            ["attached_to_doctype", "Like", "Student"],
            ["attached_to_field", "=", "image"],
        ],
        fields=["name", "file_name", "file_url"],
    )
    program_files = frappe.get_all(
        "File",
        filters=[
            ["folder", "!=", "Home/ID Cards To Sync"],
            ["attached_to_doctype", "Like", "Program Enrollment"],
            ["attached_to_field", "=", "image"],
        ],
        fields=["name", "file_name", "file_url"],
    )

    for i in files:
        frappe.delete_doc("File", i.get("name"))

    for i in program_files:
        frappe.delete_doc("File", i.get("name"))

    id_card_files = frappe.get_all(
        "File",
        filters={"folder": "Home/ID Cards To Sync"},
        fields=["name", "file_name", "file_url"],
    )
    for i in id_card_files:
        file_name = i.get("file_name")
        file_url = i.get("file_url")
        ref_no = file_name[0:6]
        if frappe.db.exists(
            "Program Enrollment", {"student": ref_no, "academic_year": "2024-2025"}
        ):
            frappe.db.set_value(
                "Program Enrollment",
                {"student": ref_no, "academic_year": "2024-2025"},
                "image",
                file_url,
            )

    for i in files:
        file_name = i.get("file_name")
        file_url = i.get("file_url")
        ref_no = file_name[0:6]
        if frappe.db.exists("Student", ref_no):
            frappe.db.set_value("Student", ref_no, "image", None)
            frappe.db.set_value("Student", ref_no, "image", file_url)
