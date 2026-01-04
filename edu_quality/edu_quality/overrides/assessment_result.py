import frappe
from education.education.doctype.assessment_result.assessment_result import (
    AssessmentResult,
)
from edu_quality.public.py.utils import extract_year_from_academic_year_name
from education.education.api import get_assessment_details, get_grade as inner_get_grade
from frappe.utils import flt
import education.education


class CustomAssessmentResult(AssessmentResult):
    def validate(self):
        # education.education.validate_student_belongs_to_group(
        #     self.student, self.student_group
        # )
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
            d.custom_scale = d.custom_scale or 1
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
            d.custom_scale = d.custom_scale or 1
            d.custom_processed_result = d.score * d.custom_scale
            d.custom_scaled_maximum_score = d.maximum_score * d.custom_scale
            d.custom_processed_grade = get_grade(
                self.grading_scale,
                (flt(d.custom_processed_result) / d.maximum_score) * 100,
                self.custom_total_processed_score,
            )
            self.total_score += d.score
            self.custom_total_processed_score += d.custom_processed_result
            self.custom_scaled_maximum_score += d.custom_scaled_maximum_score

        self.custom_processed_grade = get_grade(
            self.grading_scale,
            (self.custom_total_processed_score / self.maximum_score) * 100,
            self.custom_total_processed_score,
        )
        self.grade = get_grade(
            self.grading_scale,
            (self.total_score / self.maximum_score) * 100,
            self.total_score,
        )
        self.custom_processed_percentage = (
            self.custom_total_processed_score / self.maximum_score
        ) * 100
        return self

    def validate_processed_result(self):
        if self.docstatus in [1, 2]:
            return
        self.process_result()

    def calculate_ordering(self):
        frappe.db.sql(
            """
        Update `tabAssessment Result` 
    INNER JOIN (SELECT 
        RANK() OVER (ORDER BY custom_total_processed_score DESC) AS ranking,
        name
    FROM 
        `tabAssessment Result`
    WHERE 
        assessment_plan = %(id)s
        AND docstatus = 1 AND custom_scoring_type=%(scoring_type)s) AS ranked_table ON  `tabAssessment Result`.name = ranked_table.name
SET  `tabAssessment Result`.custom_rank = ranked_table.ranking;
""",
            values={"id": self.assessment_plan, "scoring_type": "Marks"},
            as_dict=True,
        )

    def before_submit(self, method=None):
        if self.custom_scoring_type == "Marks":
            self.process_result()
            assessment_group_doc = frappe.get_doc(
                "Assessment Group", self.assessment_group
            )
            if (
                assessment_group_doc.custom_process_passing
                and self.custom_processed_percentage
                >= assessment_group_doc.custom_passing_percentage
            ):
                self.custom_passed = 1


def get_grade(grading_scale, percentage, score):
    use_score_map = frappe.db.get_value(
        "Grading Scale", grading_scale, "custom_use_score_mapping"
    )

    if use_score_map:
        grading_scale_interval = frappe.db.get_value(
            "Grading Scale Interval",
            filters={"parent": grading_scale, "custom_score_mapping": score},
            fieldname="grade_code",
        )
        if not grading_scale_interval:
            return ""

        return grading_scale_interval or ""
    else:
        return inner_get_grade(grading_scale, percentage)
