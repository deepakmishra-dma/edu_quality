import frappe

def execute():
    pe_list = frappe.db.get_all("Program Enrollment", filters={'academic_year':"2024-2025","docstatus":0},fields=["name", "student"])
    for pe in pe_list:
        _file = frappe.get_doc(
            {
                "doctype": "File",
                "is_private":1,
                "fieldname":"image",
                "file_url": "/private/files/"+pe.student +"_2024_2025.jpg",
                "attached_to_name": pe.name,
                "attached_to_doctype": "Program Enrollment",
                "folder": "Home"
            }
        )
        _file.insert(ignore_permissions=True)