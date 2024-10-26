import frappe

def execute():
    pe_list = frappe.db.get_all("Program Enrollment", filters={'academic_year':"2024-2025","docstatus":0},fields=["name", "student"])
    for pe in pe_list:
        frappe.db.set_value("Program Enrollment", pe.name, "image", "/private/files/"+pe.student +"_2024_2025.jpg")