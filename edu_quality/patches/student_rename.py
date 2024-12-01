import frappe 

code_map = {
    "Baby Walnut Shivane" : "SH",
    "Baby Walnut Wakad": "WA",
    "Baby Walnut Fursungi": "FU",
    "Walnut School at Wakad": "WA",
    "Walnut School at Fursungi": "FU",
    "Walnut School at Shivane":"SH"
}

def execute():
    students = frappe.db.get_all("Student",fields=['name','school','reference_number'])
    for student in students:
        if student.name == "BFOA01":
            continue
        rf = code_map[student.school] + student.reference_number
        if student.name != rf:
            frappe.rename_doc("Student",student.name,rf)