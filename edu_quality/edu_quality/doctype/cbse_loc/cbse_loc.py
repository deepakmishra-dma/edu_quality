# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from edu_quality.edu_quality.server_scripts.utils import (set_user_permission, set_form_user, 
                                                          validate_aadhar, format_mobile_number,
                                                          validate_mobile_number)
from nextai.funnel.custom_trigger import trigger_event

from frappe.core.doctype.communication.email import make

class CBSELOC(Document):
   
    def after_insert(self):
        """Called after the document is inserted. Triggers autofill of student details."""
        self.autofill_student_details()        
        self.set_guardian_permission(self.form_user)
        frappe.db.set_value('CBSE LOC', self.name, 'form_hash', frappe.generate_hash(self.name, length=20))
        self.reload()
        self.send_webform_link()

    def before_save(self):
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return
        if old_doc.status == 'Not Filled' and self.status == 'Filled':
            self.send_doc_after_filling()

    def validate(self):
        self.validate_aadhar_number()
        self.validate_mobile_numbers()
        self.validate_income()


    def validate_income(self):
        if self.approximate_annual_income == "Select Income Range":
            frappe.throw("Please Select Approximate Annual Income")
    
    def validate_aadhar_number(self):
        if not validate_aadhar(self.aadhar_number):
            frappe.throw("Invalid Aadhar Number")

    def validate_mobile_numbers(self):
        invalid_numbers = []
        if self.father_mobile_number and not validate_mobile_number(self.father_mobile_number):
            invalid_numbers.append("Father's")
        if self.mother_mobile_number and not validate_mobile_number(self.mother_mobile_number):
            invalid_numbers.append("Mother's")
        
        if invalid_numbers:
            frappe.throw(f"{', '.join(invalid_numbers)} Mobile Number(s) are Invalid! [Use 10-digit mobile number, no spaces, symbols]")


        
    def set_guardian_permission(self, user):
        """Set permission for the guardian user to access the CBSE LOC document."""
        set_user_permission(user, "CBSE LOC", self.name)

    def autofill_student_details(self):
        """
        Fetches student details from the 'Student' document and updates the current document.
        Also fetches and updates guardian details if available.
        """
        student = frappe.get_doc("Student", self.student)
        
        full_name = self._construct_full_name(student.first_name, student.middle_name, student.last_name)
        self.update({
            'first_name': student.first_name,
            'middle_name': student.middle_name,
            'last_name': student.last_name,
            'full_name': full_name,
            'gender': student.gender,
            'date_of_birth': student.date_of_birth,
            'category': student.category,
            'caste': student.caste,
            'other_caste': student.other_caste,
            'aadhar_number': student.aadhaar_card_number,
            'housebuildingapt': student.address_line_1,
            'survey_nolaneroad': student.address_line_2,
            'colonysocietyarea': student.landmark,
            'city': student.city,
            'pincode': student.pincode,
            'student_status': student.student_status
        })
        
        for guard in student.guardians:
            if guard.relation.lower() in ['father', 'mother']:
                self._update_guardian_details(guard)
        
        self.get_subject_details()
        
        self.save(ignore_permissions=True)

    def get_subject_details(self):
        ac_yr = frappe.db.get_value("Academic Year", {'custom_current_academic_year': 1}, 'name')
        program_enrollment = frappe.get_doc("Program Enrollment", {'student': self.student, 'academic_year': ac_yr, 'docstatus': 1})
        i=1
        for subject in program_enrollment.courses:
            if i<7:
                self.update({
                    f"subject_{i}": subject.course
                })
            i=i+1

    def _construct_full_name(self, first_name, middle_name, last_name):
        """
        Constructs a full name from first, middle, and last names.
        
        Args:
            first_name (str): The first name of the person.
            middle_name (str): The middle name of the person.
            last_name (str): The last name of the person.
        
        Returns:
            str: The full name constructed from the given components.
        """
        parts = [first_name]
        if middle_name:
            parts.append(middle_name)
        if last_name:
            parts.append(last_name)
        return ' '.join(parts)
    
    
    @frappe.whitelist()
    def send_webform_link(self):
        trigger_event(doc=self, event_name='send_cbse_form')

    @frappe.whitelist()
    def send_doc_after_filling(self):
        try:
            template = frappe.get_doc("Email Template", "Confirm Student Details for  CBSE Board - Attachment")
            make(
                doctype="CBSE LOC",
                name=self.name,
                send_email=1,
                recipients = self.get_recipients(),
                print_format="Standard",
                print_letterhead= 0,
                read_receipt=1,
                email_template="Confirm Student Details for  CBSE Board - Attachment",
                subject = template.subject,
                message = template.response
            )
        except Exception as e:
            frappe.log_error(e)

    def get_recipients(self):
        recipients = []
        if self.father_email:
            recipients.append(self.father_email)
        if self.mother_email and self.mother_email!= self.father_email:
            recipients.append(self.mother_email)
        return ", ".join(recipients)


    def _update_guardian_details(self, guardian):
        """
        Updates the document with guardian details based on the relation (Father/Mother).
        
        Args:
            guardian (Guardian): The Guardian document object.
        """
        relation = guardian.relation.lower()
        doc = frappe.get_doc("Guardian", guardian.guardian)
        if relation == 'father':
            self.form_user = doc.user 
        else:
            if not self.form_user:
                self.form_user = doc.user
        full_name = self._construct_full_name(doc.first_name, doc.middle_name, doc.last_name)
        details = {
            f'{relation}_first_name': doc.first_name,
            f'{relation}_middle_name': doc.middle_name,
            f'{relation}_last_name': doc.last_name,
            f'{relation}_full_name': full_name,
            f'{relation}_mobile_number': format_mobile_number(doc.mobile_number),
            f'{relation}_email': doc.email_address
        }
        
        self.update(details)

@frappe.whitelist(allow_guest=True)
def get_form_details(hash):
    """
    Retrieves the CBSE LOC document details based on the provided hash.
    
    Args:
        hash (str): The unique hash associated with the CBSE LOC document.
    
    Returns:
        dict: A dictionary containing the form user details.
    
    Raises:
        frappe.PermissionError: If the CBSE LOC document with the provided hash is not found.
    """
    if not frappe.db.exists("CBSE LOC", {'form_hash': hash}):
        frappe.throw("Form Not Found!")
    docname = frappe.db.get_value("CBSE LOC", {'form_hash': hash}, 'name')
    return set_form_user("CBSE LOC", docname)


@frappe.whitelist()
def generate_confirmations(program):
    """
    Generates CBSE LOC documents for students enrolled in the given program.
    
    Args:
        program (str): The name of the program for which CBSE LOCs need to be generated.
    
    Returns:
        dict: A dictionary containing the status (success or failure) and an error message (if applicable).
    """
    try:
        frappe.enqueue(student_confirmation_generation, program=program, queue='long')
        return {'status': 1}
    except Exception as e:
        return {'status': 0, 'error': str(e)}
    


def student_confirmation_generation(program,status="Current student"):
    """
    Helper function to generate CBSE LOC documents for students enrolled in the given program.
    
    Args:
        program (str): The name of the program for which CBSE LOCs need to be generated.
    """
    ac_yr = frappe.db.get_value("Academic Year", {'custom_current_academic_year': 1}, 'name')
    students = frappe.get_all("Program Enrollment", filters={'program': program, 'docstatus': 1, 'academic_year': ac_yr, 'custom_status': status}, fields=['student'])
    for student in students:
        try:
            if not frappe.db.exists("CBSE LOC", {'student': student.student}):
                doc = frappe.new_doc("CBSE LOC")
                doc.student = student.student
                doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error("CBSE", e)
