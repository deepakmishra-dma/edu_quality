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
            self.validate_processed_result()

        if self.custom_scoring_type == "Grades":
            self.duplicate_grades()

        self.validate_duplicate()

    def calculate_scaled_maximum_score(self):
        total_scaled_max_score = 0
        for d in self.details:
            total_scaled_max_score += d.maximum_score * d.custom_scale
        self.custom_scaled_maximum_score = total_scaled_max_score

    def duplicate_grades(self):
        if self.docstatus in [1, 2]:
            return
        for d in self.details:
            d.custom_processed_grade = d.grade

    def process_result(self):
        self.total_score = 0.0
        self.custom_total_processed_score = 0.0
        self.custom_scaled_maximum_score = 0.0
        for d in self.details:
            d.custom_processed_result = d.score * d.custom_scale
            d.custom_scaled_maximum_score = d.maximum_score * d.custom_scale
            d.custom_processed_grade = get_grade(
                self.grading_scale,
                (flt(d.custom_processed_result) / d.maximum_score) * 100,
            )
            self.total_score += d.score
            self.custom_total_processed_score += d.custom_processed_result
            self.custom_scaled_maximum_score += d.custom_scaled_maximum_score

        self.custom_processed_grade = get_grade(
            self.grading_scale,
            (self.custom_total_processed_score / self.maximum_score)
            * 100,
        )
        self.custom_processed_percentage = (
            self.custom_total_processed_score / self.maximum_score
        ) * 100
        return self

    def validate_processed_result(self):
        if self.docstatus in [1, 2]:
            return
        self.process_result()

    def before_submit(self, method=None):
        if self.custom_scoring_type == "Marks":
            self.process_result()
            assessment_group_doc = frappe.get_doc("Assessment Group", self.assessment_group)
            if (
                assessment_group_doc.custom_process_passing
                and self.custom_processed_percentage
                >= assessment_group_doc.custom_passing_percentage
            ):
                self.custom_passed = 1
