import frappe
from collections import Counter


@frappe.whitelist(allow_guest=True)
def get_student_data(student):
    student = frappe.get_doc("Student", student, ignore_permissions=True)
    return student.as_dict()


@frappe.whitelist()
def get_student_details(program):
    ay = frappe.get_value("Academic Year", {"custom_current_academic_year": 1}, "name")
    batches = set(frappe.get_all(
        "Student Group", {"program": program, "academic_year": ay}, pluck="batch"
    ))
    # get all students in the program
    students = get_students(program, ay)
    division_data = {}

    for batch in batches:
        # filter student by batch
        st_data = [s for s in students if s.batch == batch]
        divs = frappe.get_all(
            "Student Group",
            {"batch": batch, "program": program, "academic_year": ay},
            ["name"],
        )
        no_of_divs = len(divs)
        # split students to fit in the divisions
        split_students = [st_data[i::no_of_divs] for i in range(no_of_divs)]

        for div in divs:
            student_data = split_students.pop(0)
            gender_counts = Counter(s.gender for s in student_data)
            house_counts = Counter(s.school_house for s in student_data)
            division_data.setdefault(div.name, {}).update({
                "students": student_data,
                "no_of_students": len(student_data),
                "boys": gender_counts["Male"],
                "girls": gender_counts["Female"],
                "yellow": house_counts["Yellow"],
                "green": house_counts["Green"],
                "red": house_counts["Red"],
                "blue": house_counts["Blue"],
            })

    # Cache the data for 5 minutes to use if clicked okay in the dialog
    rs = frappe.cache()
    data = frappe.json.dumps(division_data)
    rs.set(program, data, 300)
    return division_data


def get_students(program, ay):
    return frappe.db.sql(
        """
        SELECT s.name, s.first_name, s.gender, p.school_house, d.batch
        FROM `tabStudent` as s
        LEFT JOIN `tabProgram Enrollment` as p
        ON s.name = p.student
        LEFT JOIN `tabStudent Group` as d
        ON p.student_group = d.name
        WHERE p.program = %s and p.academic_year = %s and s.student_status != 'Cancelled' 
        GROUP BY d.batch, p.school_house, s.gender, s.name
        """,
        (program, ay),
        as_dict=True,
    )


@frappe.whitelist()
def shuffle_division_data(program):
    try:
        data = frappe.cache().get(program)
        division_data = frappe.json.loads(data)
        for division, details in division_data.items():
            students = details.get("students")
            div = frappe.get_doc("Student Group", division)
            div.students = []
            for student in students:
                div.append(
                    "students",
                    {
                        "student": student.get("name"),
                    },
                )
            div.save()
        return "Division shuffled successfully"
    except Exception as e:
        frappe.log_error("Shuffle Division Data Error", frappe.get_traceback())
        return "Error while shuffling division data"
