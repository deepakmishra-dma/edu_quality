import frappe

from frappe.utils import getdate
import datetime
from edu_quality.api.print_id_card import generate_permanent_id_cards
from erpnext.accounts.doctype.payment_request.payment_request import get_gateway_details
from erpnext.accounts.party import get_party_bank_account
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)


@frappe.whitelist()
def validate_bank_account(student):
    return frappe.db.exists("Bank Account", {"party": student})

@frappe.whitelist()
def cancel_student(student,academic_year,fee_collection):
    try:
        if frappe.db.exists("Program Enrollment",{'student':student,'academic_year':academic_year,'docstatus':1}):
            frappe.db.set_value("Program Enrollment",{'student':student,'academic_year':academic_year,'docstatus':1},'docstatus',2)
        frappe.db.set_value("Student",student,'enabled',0)
        frappe.db.set_value("Student",student,"student_status","Cancelled")
        fees_list = frappe.db.get_all("Fees",filters={'docstatus':1,'student':student})
        for fee in fees_list:
            if frappe.db.exists("Fee Component",[['parent','=',fee.name],['fees_category','like','%DEPOSIT%']]):
                deposit = frappe.db.get_value("Fee Component",[['parent','=',fee.name],['fees_category','like','%DEPOSIT%']],'amount')
                refund_deposit(student,fee.name,deposit)
        return 1
    except Exception as e:
        frappe.logger("Cancel").exception(e)
        return 0

def refund_deposit(student,fee,amount):
    gateway_account = get_gateway_details({}) or frappe._dict()
    pr = frappe.new_doc("Payment Request")
    ref_doc = frappe.get_doc("Fees",fee)
    bank_account = (
        get_party_bank_account("Student", student)
    )
    pr.update(
        {
            "payment_gateway_account": gateway_account.get("name"),
            "payment_gateway": gateway_account.get("payment_gateway"),
            "payment_account": gateway_account.get("payment_account"),
            "payment_channel": gateway_account.get("payment_channel"),
            "payment_request_type": "Outward",
            "currency": "INR",
            "grand_total": amount,
            "email_to": student+"@walnutedu.in",
            "subject": "Deposit Refund For for {0}".format(student),
            "message": "Deposit Refund",
            "reference_doctype": "Fees",
            "reference_name": fee,
            "party_type": "Student",
            "party": student,
            "bank_account": bank_account,
            "company": ref_doc.get("company"),
        }
    )

    # Update dimensions
    pr.update(
        {
            "cost_center": ref_doc.get("cost_center"),
            "project": ref_doc.get("project"),
        }
    )

    for dimension in get_accounting_dimensions():
        pr.update({dimension: ref_doc.get(dimension)})

    pr.insert(ignore_permissions=True)
    pr.submit()
    

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
    add_student_log(doc, doc.student_group, True)
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
    add_student_log(doc, division)


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
        comment = f"Student: {student.student_name}({student.name}) is Removed from division {division}"
    else:
        comment = f"Student: {student.student_name}({student.name}) is Added to division {division}"
    frappe.get_doc({
        'doctype': 'Comment',
        'comment_type': 'Info',
        'reference_doctype': 'Student Group',
        'reference_name': division,
        'content': comment,
    }).insert(ignore_permissions=True)


def add_student_log(doc, division, is_removed=False):
    """
    doc: Program Enrollment
    division: Division
    this function adds student log
    """
    student_info = f"Student: {doc.student_name}({doc.name})"
    action = "Removed from" if is_removed else "Added to"
    log = f"{student_info} is {action} division {division}"

    doc_info = {
        'doctype': 'Student Log',
        'student': doc.student,
        'type': 'General',
        'academic_year': doc.academic_year,
        'academic_term': doc.academic_term,
        'program': doc.program,
        'student_batch': doc.student_batch_name,
        'log': log,
        'date': frappe.utils.now_datetime(),
    }

    frappe.get_doc(doc_info).insert(ignore_permissions=True)