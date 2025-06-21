import frappe 

def on_cancel(doc,method=None):
    try:
        remove_student_from_divison(doc.student_group,doc.student)
    except Exception as e:
        frappe.throw("Error:" + str(e))


def remove_student_from_divison(student,division):
    if frappe.db.exists("Student Group Student",{"parent":division,"student":student}):
        frappe.delete_doc("Student Group Student",{"parent":division,"student":student})
