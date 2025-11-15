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
        total = 0
        total_scaled_max_score = 0
        for detail in self.details:
            if self.custom_scoring_type != "Marks":
                return

            score = detail.get("score")
            scale = detail.get("custom_scale") or 1
            maximum_score = detail.get("maximum_score")

            if not detail.get("custom_is_absent"):
                detail.custom_processed_result = score * scale

                total += score * scale

            total_scaled_max_score += maximum_score * scale

        if self.custom_scoring_type != "Marks":
            return

        self.custom_total_processed_score = total
        processed_percentage = (total / total_scaled_max_score) * 100

        self.custom_processed_percentage = (
            0 if total_scaled_max_score == 0 else processed_percentage
        )
        assessment_group_doc = frappe.get_doc("Assessment Group", self.assessment_group)

        if (
            assessment_group_doc.custom_process_passing
            and processed_percentage >= assessment_group_doc.custom_passing_percentage
        ):
            self.custom_passed = 1
