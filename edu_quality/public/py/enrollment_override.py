import frappe
from education.education.doctype.program_enrollment.program_enrollment import ProgramEnrollment
from frappe.utils import comma_and, get_link_to_form, getdate
from frappe import _

class CustomProgramEnrollment(ProgramEnrollment):
    def validate_academic_year(self):
        start_date, end_date = frappe.db.get_value(
            "Academic Year", self.academic_year, ["year_start_date", "year_end_date"]
        )
        if self.enrollment_date:
            # if start_date and getdate(self.enrollment_date) < getdate(start_date):
            #     frappe.throw(
            #         _(
            #             "Enrollment Date cannot be before the Start Date of the Academic Year {0}"
            #         ).format(get_link_to_form("Academic Year", self.academic_year))
            #     )

            if end_date and getdate(self.enrollment_date) > getdate(end_date):
                frappe.throw(
                    _("Enrollment Date cannot be after the End Date of the Academic Term {0}").format(
                        get_link_to_form("Academic Year", self.academic_year)
                    )
                )

    def validate_academic_term(self):
        start_date, end_date = frappe.db.get_value(
            "Academic Term", self.academic_term, ["term_start_date", "term_end_date"]
        )
        if self.enrollment_date:
            # if start_date and getdate(self.enrollment_date) < getdate(start_date):
            #     frappe.throw(
            #         _(
            #             "Enrollment Date cannot be before the Start Date of the Academic Term {0}"
            #         ).format(get_link_to_form("Academic Term", self.academic_term))
            #     )

            if end_date and getdate(self.enrollment_date) > getdate(end_date):
                frappe.throw(
                    _("Enrollment Date cannot be after the End Date of the Academic Term {0}").format(
                        get_link_to_form("Academic Term", self.academic_term)
                    )
                )
    
