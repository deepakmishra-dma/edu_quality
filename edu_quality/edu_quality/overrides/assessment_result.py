import frappe
from education.education.doctype.assessment_result.assessment_result import (
    AssessmentResult,
)
from edu_quality.public.py.utils import extract_year_from_academic_year_name
from education.education.api import get_assessment_details, get_grade
from frappe.utils import flt
import education.education


class CustomAssessmentResult(AssessmentResult):
    def validate(self):
        education.education.validate_student_belongs_to_group(
            self.student, self.student_group
        )
        self.validate_maximum_score()
        if self.custom_scoring_type == "Marks":
            self.validate_grade()
        self.validate_duplicate()

    def before_submit(self, method=None):
        for detail in self.details:
            if self.custom_scoring_type != "Marks":
                return
            
            score = detail.get("score")
            scale = detail.get("scale")
            if detail.get("custom_is_absent") == 0:
                frappe.db.set_value(
                    "Assessment Result Detail",
                    detail.get("name"),
                    "custom_processed_result",
                    score * scale,
                )
