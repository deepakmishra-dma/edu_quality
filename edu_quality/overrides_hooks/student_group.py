import frappe


def on_update(doc, method=None):
    for student in doc.students:
        prod_doc = frappe.get_doc("Program Enrollment", {"student": student.student,"student_group":doc.name})
        if str(prod_doc.roll_no) != str(student.group_roll_number):
            prod_doc.roll_no = student.group_roll_number
            prod_doc.save()
