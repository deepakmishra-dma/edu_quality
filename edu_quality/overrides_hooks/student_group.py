import frappe


def on_update(doc, method=None):
    for student in doc.students:
        try:
            prod_doc = frappe.get_doc("Program Enrollment", {"student": student.student,"student_group":doc.name})
            if str(prod_doc.roll_no) != str(student.group_roll_number):
                prod_doc.roll_no = student.group_roll_number
                prod_doc.save()
        except Exception as e:
            continue       



def before_save(doc,method=None):
    if doc.custom_max_groups_allowed and len(doc.students):
        max_grp_value = doc.custom_max_groups_allowed
        idx=1
        for student in doc.students:
            if not student.get('custom_group_allocated'):
                student.custom_group = idx
                student.custom_group_allocated = 1
            idx+=1
            if idx > max_grp_value:
                idx = 1
            
            
        
       