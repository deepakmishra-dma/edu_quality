import frappe
from education.education.doctype.assessment_group.assessment_group import (
    AssessmentGroup,
)
from edu_quality.public.py.utils import extract_year_from_academic_year_name


class CustomAssessmentGroup(AssessmentGroup):
    def autoname(self):
        short_acad_year = extract_year_from_academic_year_name(
            self.custom_academic_year
        )
        self.name = f"{self.name} {short_acad_year}"

    def before_validate(self):
        if frappe.db.exists(
            "Assessment Group",
            {
                "custom_order": self.custom_order,
                
                "custom_academic_year": self.custom_academic_year,
            },
        ):
            frappe.throw("Order for the class already exists")

    pass
