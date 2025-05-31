import frappe

from frappe.utils import getdate
import datetime
from edu_quality.api.print_id_card import generate_permanent_id_cards

@frappe.whitelist()
def mark_entry(student, status, reason=None, date=None, time=None):
    if not date:
        date = getdate()
    if not time:
        time = datetime.datetime.now().strftime("%H:%M:%S")

    try:
        if frappe.db.exists("Attendance Entry", {"student": student, "date": date}):
            entry = frappe.get_doc(
                "Attendance Entry", {"student": student, "date": date}
            )
            entry.append(
                "absent_and_delays",
                {
                    "reason": reason,
                    "status": status,
                    "timestamp": date + " " + time,
                    "user": frappe.session.user,
                },
            )
            entry.flags.ignore_mandatory = True
            entry.save(ignore_permissions=True)
        else:
            entry = frappe.new_doc("Attendance Entry")
            entry.student = student
            entry.date = date
            entry.append(
                "absent_and_delays",
                {
                    "reason": reason,
                    "status": status,
                    "timestamp": date + " " + time,
                    "user": frappe.session.user,
                },
            )
            entry.insert(ignore_permissions=True)
        return True
    except Exception as e:
        frappe.logger("entry").exception(e)
        return False


@frappe.whitelist()
def swap_division(**kwargs):
    try:
        division = kwargs.get("division")
        student = kwargs.get("student_to_swap")
        pe = kwargs.get("program_enrollment")
        pe_doc = frappe.get_doc("Program Enrollment", pe)

        if division:
            # remove from current division
            remove_from_division(pe_doc)
            # update student group in program enrollment
            frappe.db.set_value("Program Enrollment", pe, "student_group", division) 
            # add to new division 
            add_to_division(pe_doc, division)
            return True
        elif student:
            # get the program enrollment of the student to swap
            swap_pe = frappe.get_doc("Program Enrollment", {"student": student, "academic_year": pe_doc.academic_year})
            # swap the division
            swap_student_division(pe_doc, swap_pe)
            return True
    except:
        frappe.db.rollback()
        frappe.log_error('Error while swapping division', frappe.get_traceback())
        return False


def remove_from_division(doc):
    """
    doc: Program Enrollment
    division: Division
    this function removes the student from the division
    """
    division = frappe.get_doc("Student Group", doc.student_group)
    roll_no = 0
    for d in division.students:
        if d.student == doc.student:
            division.remove(d)
            roll_no = d.group_roll_number
            break
    division.save()
    add_comment_in_division(doc, doc.student_group, True)
    return roll_no


def add_to_division(doc, division, roll_no=None):
    """
    doc: Program Enrollment
    division: Division
    this function adds the student to the division
    """
    sg = frappe.get_doc("Student Group", division)
    roll_numbers = set(d.group_roll_number for d in sg.students if d.group_roll_number)
    if not roll_no:
        next_roll_number = next((i for i in range(1, len(roll_numbers) + 2) if i not in roll_numbers), 1)
    else:
        next_roll_number = roll_no
    
    sg.append("students", {
        "student": doc.student,
        "student_name": doc.student_name,
        "group_roll_number": next_roll_number,
        "active": 1
    })
    sg.save()
    add_comment_in_division(doc, division)


def swap_student_division(pe_doc_1, pe_doc_2):
    """
    pe_doc_1: Program Enrollment of student 1
    pe_doc_2: Program Enrollment of student 2
    this function swaps the student division
    """
    division_1 = frappe.get_doc("Student Group", pe_doc_1.student_group)
    division_2 = frappe.get_doc("Student Group", pe_doc_2.student_group)
    # remove student 1 from current division
    rno1 = remove_from_division(pe_doc_1)
    # update student group in program enrollment of student 1
    frappe.db.set_value("Program Enrollment", pe_doc_1.name, "student_group", pe_doc_2.student_group)
    # update tiffin rack no
    frappe.db.set_value("Program Enrollment", pe_doc_1.name, "tiffin_rack_no", pe_doc_2.tiffin_rack_no)
    # remove student 2 from current division
    rno2 = remove_from_division(pe_doc_2)
    # update student group in program enrollment of student 2
    frappe.db.set_value("Program Enrollment", pe_doc_2.name, "student_group", pe_doc_1.student_group)
    # update tiffin rack no
    frappe.db.set_value("Program Enrollment", pe_doc_2.name, "tiffin_rack_no", pe_doc_1.tiffin_rack_no)
    # add student 1 to student 2 division
    add_to_division(pe_doc_1, division_2.name, rno2)
    # add student 2 to student 1 division
    add_to_division(pe_doc_2, division_1.name, rno1)
    # generate permanent id cards
    generate_permanent_id_cards(enrollments=[pe_doc_1.name, pe_doc_2.name])

    # send email to bcc admin of school
    send_email_for_division_swap(pe_doc_1)
    send_email_for_division_swap(pe_doc_2)
    return True


def send_email_for_division_swap(pe_doc_1):
    """
    pe_doc_1: Program Enrollment of student 1
    this function sends email to students for division swap
    """
    student = frappe.get_doc("Student", pe_doc_1.student)
    guardian_email = [i.guardian_name for i in student.guardians]
    guardian = frappe.get_all(
        doctype="Guardian",
        fields=["email_address"],
        filters=[["guardian_name", "in", guardian_email]],
    )
    recipients = [i.email_address for i in guardian]
    school_details = frappe.get_doc("School", pe_doc_1.custom_school)
    bcc_admin = school_details.get("bcc_email_address")
    frappe.sendmail(
        recipients=recipients,
        bcc=[bcc_admin],
        subject="Division Swap",
        message=f"Dear {student.student_name},\n\nYour division has been swapped successfully. Please find the details below:\n\nDivision: {pe_doc_1.student_group}\n\nRegards,\n{school_details.name}",
    )


def add_comment_in_division(student, division, is_removed=False):
    """
    Adds a comment in the division for a student.

    Args:
        student (object): The student object.
        division (str): The division name.
        is_removed (bool, optional): Flag to indicate if the student is removed. Defaults to False.
    """
    if is_removed:
        comment = f"Student: {student.student_name}({student}) is Removed from division {division}"
    else:
        comment = f"Student: {student.student_name}({student}) is Added to division {division}"
    frappe.get_doc({
        'doctype': 'Comment',
        'comment_type': 'Info',
        'reference_doctype': 'Student Group',
        'referenc_name': division,
        'content': comment,
    }).insert(ignore_permissions=True)