# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CBSEConfirmation(Document):
    """
    A Document class representing CBSE Confirmation details.
    Automatically fills student details upon insertion.
    """
    def after_insert(self):
        """Called after the document is inserted. Triggers autofill of student details."""
        self.autofill_student_details()
        self.form_hash = frappe.generate_hash(self.name, length=20)

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
            'pincode': student.pincode
        })
        
        for guard in student.guardians:
            if guard.relation.lower() in ['father', 'mother']:
                self._update_guardian_details(guard)
            
        
        self.save(ignore_permissions=True)

    def _construct_full_name(self, first_name, middle_name, last_name):
        """
        Constructs a full name from first, middle, and last names.
        """
        parts = [first_name]
        if middle_name:
            parts.append(middle_name)
        if last_name:
            parts.append(last_name)
        return ' '.join(parts)

    def _update_guardian_details(self, guardian):
        """
        Updates the document with guardian details based on the relation (Father/Mother).
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
            f'{relation}_mobile_number': doc.mobile_number,
            f'{relation}_email': doc.email_address
        }
        
        self.update(details)

@frappe.whitelist()
def get_form_details(hash):
    pass