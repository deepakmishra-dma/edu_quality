import frappe

school_map = {
    "Walnut School at Wakad": "Baby Walnut Wakad",
    "Walnut School at Fursungi": "Baby Walnut Fursungi",
    "Walnut School at Shivane":"Baby Walnut Shivane"
}


def execute():
    program_enrollment_list = frappe.db.get_all("Program Enrollment",filters = [["Program Enrollment","academic_year","=","2023-2024"],["Program Enrollment","program","like","%Nursery%"]],fields=['name','program','custom_school','student_group'])
    for pe in program_enrollment_list:
        school = school_map[pe.custom_school]
        program = "Nursery-" + school
        if not frappe.db.exists("Program",{'name': program}):
            prog = frappe.new_doc("Program")
            prog.program_name = "Nursery"
            prog.sequence = 1
            prog.school = school
            prog.class_group = "KG"
            prog.insert(ignore_permissions=True)
        division = pe.student_group[0]+"-Nursery-" + school+"-2023-2024"
        if not frappe.db.exists("Student Group",{'name': division}):
            div = frappe.new_doc("Student Group")
            div.student_group_name = pe.student_group[0]
            div.program = program
            div.custom_school = school 
            div.academic_year = "2023-2024"
            div.group_based_on = "Batch"
            div.batch = frappe.db.get_value("Student Group",{'name': pe.student_group},'batch')
            div.max_strength = frappe.db.get_value("Student Group",{'name': pe.student_group},'max_strength')
            div.insert(ignore_permissions=True)
        frappe.db.set_value("Program Enrollment",pe.name,{
            "custom_school": school,
            "program": program,
            "student_group": division
        })
    program_enrollment_list = frappe.db.get_all("Program Enrollment",filters = [["Program Enrollment","academic_year","=","2023-2024"],["Program Enrollment","program","like","%Junior KG%"]],fields=['name','program','custom_school','student_group'])
    for pe in program_enrollment_list:
        school = school_map[pe.custom_school]
        program = "Junior KG-" + school
        if not frappe.db.exists("Program",{'name': program}):
            prog = frappe.new_doc("Program")
            prog.program_name = "Nursery"
            prog.sequence = 1
            prog.school = school
            prog.class_group = "KG"
            prog.insert(ignore_permissions=True)
        division = pe.student_group[0]+"-Junior KG-" + school+"-2023-2024"
        if not frappe.db.exists("Student Group",{'name': division}):
            div = frappe.new_doc("Student Group")
            div.student_group_name = pe.student_group[0]
            div.program = program
            div.custom_school = school 
            div.academic_year = "2023-2024"
            div.group_based_on = "Batch"
            div.batch = frappe.db.get_value("Student Group",{'name': pe.student_group},'batch')
            div.max_strength = frappe.db.get_value("Student Group",{'name': pe.student_group},'max_strength')
            div.insert(ignore_permissions=True)
        frappe.db.set_value("Program Enrollment",pe.name,{
            "custom_school": school,
            "program": "Junior KG-" + school,
            "student_group": pe.student_group[0]+"-Junior KG-" + school+"-2023-2024"
        })
    