import frappe 

school_map = {
    "Walnut School at Wakad": "Baby Walnut Wakad",
    "Walnut School at Fursungi": "Baby Walnut Fursungi",
    "Walnut School at Shivane": "Baby Walnut Shivane"
}

def execute():

    junior_kg_applicants = frappe.db.get_all("Student Applicant",filters=[["Student Applicant","application_status","!=","Admitted"],["Student Applicant","program","like","%Junior KG-Walnut School%"]])
    process_data(junior_kg_applicants,"Junior KG-")
    senior_kg_applicants = frappe.db.get_all("Student Applicant",filters=[["Student Applicant","application_status","!=","Admitted"],["Student Applicant","program","like","%Senior KG-Walnut School%"]])
    process_data(senior_kg_applicants,"Senior KG-")
    nursery_applicants = frappe.db.get_all("Student Applicant",filters=[["Student Applicant","application_status","!=","Admitted"],["Student Applicant","program","like","%Nursery-Walnut School%"]])
    process_data(nursery_applicants,"Nursery-")

def process_data(applicants,class_name):
    for applicant in applicants:
            doc = frappe.get_doc("Student Applicant",applicant.name)
            doc.school = school_map[doc.school]
            doc.program = class_name + doc.school
            doc.fee_structure = ""
            doc.academic_year = "2024-2025"
            doc.save(ignore_permissions=True)



