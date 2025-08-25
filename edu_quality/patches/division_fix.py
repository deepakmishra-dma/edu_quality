import frappe 

def execute():

    pe_list = frappe.db.get_all("Program Enrollment",{'program': ['like', '%kg%'], 'academic_year': '2024-2025','docstatus':1},['name', 'student', 'program', 'custom_school', 'student_group'])

    for pe in pe_list:
        if not frappe.db.exists("Student Group Student",{'student':pe.student,'parent':pe.student_group}):
            div = frappe.get_doc("Student Group",pe.student_group)
            div.append("students",{
                'student':pe.student
            })
            try:
                div.save(ignore_permissions=True)
            except Exception as e:
                frappe.logger('div_fix').exception(e)
                frappe.logger('div_fix').exception(div.name)
                continue
        