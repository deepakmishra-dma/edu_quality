import frappe

def create_undertaking(student):
    student_status = frappe.db.get_value("Student", student, "student_status")
    academic_year = None
    if student_status == "New student":
        academic_year = frappe.db.get_value("Academic Year", {"custom_next_academic_year": 1}, "name")
    else:
        academic_year = frappe.db.get_value("Academic Year", {"custom_current_academic_year": 1}, "name")

    class_name = frappe.db.get_value("Program Enrollment", {"student": student.name, "academic_year": academic_year}, "program")
    fathers_name = frappe.db.get_value(
        "Student Guardian", {"parent": student.name, "relation": "Father"}, "guardian_name"
    )
    mothers_name = frappe.db.get_value(
        "Student Guardian", {"parent": student.name, "relation": "Mother"}, "guardian_name"
    )
    template = frappe.db.get_value(
        "Rules and Regulation Template", {"class": class_name, "status": student_status, "academic_year":academic_year}, "name"
    )
    
    payment_term = frappe.db.get_value("Payment Entry", {"party": student.name, "docstatus": 1}, "payment_term")
    submitted_date = frappe.db.get_value("Payment Entry", {"party": student.name, "docstatus": 1}, "posting_date")
    if not frappe.db.exists(
        "Rules and Regulation Submission",
        {"student": student.name, "program": class_name, "payment_term": payment_term},
    ):
        new_doc = frappe.new_doc("Rules and Regulation Submission")
        new_doc.student = student.name
        new_doc.reference_no = student.reference_number
        new_doc.fathers_name = fathers_name
        new_doc.mothers_name = mothers_name
        new_doc.program = class_name
        new_doc.submitted_with_response = "Yes"
        new_doc.rules_and_regulation_template = template
        new_doc.submitted_date = submitted_date
        new_doc.payment_term = payment_term
        new_doc.save(ignore_permissions=True)
        

def execute():     
    # Get all students from Payment Entry where party_type is 'Student'
    data = frappe.db.get_all("Payment Entry", filters={'party_type': "Student"}, pluck='party')
    
    # Get all students that already have a Rules and Regulation Submission
    submitted_students = frappe.db.get_all("Rules and Regulation Submission", filters={'student': ['in', data]}, pluck='student')
    
    # Find students who do not have a Rules and Regulation Submission
    students = set(data) - set(submitted_students)
    
    result = frappe.get_all("Student", {"student_status": ["in", ["Current student", "Defaulter", "New student"]], "name": ["in", students]}, ["name", "student_status", "reference_number"])
    for student in result:
        create_undertaking(student)
