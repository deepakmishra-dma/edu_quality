import frappe
from education.education.doctype.assessment_result.assessment_result import (
    AssessmentResult,
)
from edu_quality.public.py.utils import extract_year_from_academic_year_name


class CustomAssessmentResult(AssessmentResult):
    def before_submit(self, method=None):
        for detail in self.details:
            score = detail.get("score")
            scale = detail.get("scale")
            if detail.get("custom_is_absent") == 0:
                frappe.db.set_value(
                    "Assessment Result Detail",
                    detail.get("name"),
                    "custom_processed_result",
                    score * scale,
                )
