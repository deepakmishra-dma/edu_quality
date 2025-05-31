import frappe 

def execute():
    student_list = frappe.db.get_all("Student",limit=10)
    for student in student_list:
        try:
            latest_enrollment = frappe.get_all("Program Enrollment",filters={'student':student.name,'docstatus':1},fields=['name','academic_year'],order_by='academic_year')
            if latest_enrollment:
                frappe.db.set_value("Student",student.name,"custom_academic_year",latest_enrollment[-1].academic_year)
            doc = frappe.get_doc("Student",student.name)
            for guardian in doc.guardians:
                guardian.email = 'e'
                doc.save(ignore_permissions=True)
                break
        except Exception as e:
            frappe.logger('student_update').exception(e)