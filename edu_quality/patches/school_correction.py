import frappe 

def execute():
    return
    data = get_data()
    process_data(data)
    

school_map = {
    "Walnut School at Wakad": "Baby Walnut Wakad",
    "Walnut School at Fursungi": "Baby Walnut Fursungi",
    "Walnut School at Shivane": "Baby Walnut Shivane"
}

def get_data():
    data = frappe.db.get_all("Program Enrollment", filters = [
        ["program", "Like", "Nursery"],
        ["program","Like","KG"],
    ],fields = ["student_group","custom_school","program","student","academic_year","name"])
    return data


def process_data(data):
    for student in data:
        new_school = school_map[student.custom_school] 
        new_class = create_classes_if_not_exist(student.program,new_school)
        new_division = create_divisions_if_not_exist(student.student_group,new_school,new_class,student.academic_year)
        frappe.db.set_value("Program Enrollment",student.name,{
            "custom_school":new_school,
            "program":new_class,
            "student_group":new_division
        })
        

        
def create_classes_if_not_exist(program,new_school):
    current = frappe.get_doc("Program", program)
    if frappe.db.exists("Program", {'school':new_school,"program_name":current.program_name}):
        return frappe.db.get_value("Program", {'school':new_school,"program_name":current.program_name},"name")
    else:
        doc = frappe.get_doc({
            "doctype":"Program",
            "school":new_school,
            "program_name":current.program_name,
            "reference_series":current.reference_series,
            "sequence":current.sequence,
            "class_group":current.class_group,
            "custom_email_template": current.custom_email_template,
            "custom_date_start": current.custom_date_start,
            "custom_date_end": current.custom_date_end,
            })
        doc.insert(ignore_permissions=True)
        return doc.name
        


def create_divisions_if_not_exist(group,new_school,new_class,academic_year):
    group = frappe.get_doc("Student Group", group)
    if frappe.db.exists("Student Group", {"academic_year":academic_year,
                                          "custom_school":new_school,
                                          "student_group_name":group.student_group_name,
                                          "program":new_class}):
        return frappe.db.get_value("Student Group", {"academic_year":academic_year,
                                                     "custom_school":new_school,
                                                     "student_group_name":group.student_group_name,
                                                     "program":new_class})
    else:
        doc = frappe.get_doc({
            "doctype":"Student Group",
            "custom_school":new_school,
            "program":new_class,
            "academic_year":academic_year,
            "student_group_name":group.student_group_name,
            "max_strength": group.max_strength,
            "current_count": group.current_count,
            "batch": group.batch,
            "start_time": group.start_time,
            "end_time": group.end_time
            })
        doc.insert(ignore_permissions=True)
        return doc.name
