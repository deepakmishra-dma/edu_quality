# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from edu_quality.public.py.utils import get_div_students
from pypika.analytics import Rank
from frappe.query_builder import Order


class AssessmentGroupResult(Document):
    def __setup__(self):
        self.onload()

    def onload(self):
        """Load Existing results for quick view"""
        self.load_results()

    def load_results(self):
        """Load `results` from the database"""
        self.results = []
        plans = get_all_plans(self)
        results = get_all_results(self, plans)

        for result in results:
            self.append("results", result)
        return results

    def calculate_class_rank(self):
        assess_gr_qb = frappe.qb.DocType("Assessment Group Result")
        query = (
            frappe.qb.from_(assess_gr_qb)
            .where((assess_gr_qb.docstatus.isin([0, 1])))
            .select(
                assess_gr_qb.combined_percentage,
                assess_gr_qb.name,
                Rank()
                .over()
                .orderby(assess_gr_qb.combined_percentage, order=Order.desc)
                .as_("rank"),
            )
        )
        final_query = (
            frappe.qb.from_(query).where((self.name == query.name)).select(query.star)
        )

        data = final_query.run(as_dict=True)
        if data:
            return data[0].get("rank")
        return None

    def calculate_div_rank(self):
        assess_gr_qb = frappe.qb.DocType("Assessment Group Result")
        student = self.student
        academic_year = self.academic_year

        division = frappe.db.get_value(
            "Program Enrollment",
            {"student": student, "academic_year": academic_year, "docstatus": 1},
            "student_group",
        )
        if not division:
            frappe.throw("Program Enrollment not found")
        students = get_div_students(division)
        student_list = [student.get("student") for student in students]

        query = (
            frappe.qb.from_(assess_gr_qb)
            .where(
                (assess_gr_qb.docstatus.isin([0, 1]))
                & (assess_gr_qb.student.isin(student_list or [None]))
            )
            .select(
                assess_gr_qb.combined_percentage,
                assess_gr_qb.name,
                Rank()
                .over()
                .orderby(assess_gr_qb.combined_percentage, order=Order.desc)
                .as_("rank"),
            )
        )
        final_query = (
            frappe.qb.from_(query).where((self.name == query.name)).select(query.star)
        )

        data = final_query.run(as_dict=True)
        if data:
            return data[0].get("rank")
        return None

    def calculate_total_score(self):
        total_max_score = 0
        total_processed_score = 0

        for result in self.results:
            if result.scoring_type == "Marks":
                total_max_score += result.maximum_score
                total_processed_score += result.total_score

        self.combined_total_score = total_processed_score
        self.combined_maximum_score = total_max_score
        if total_max_score:
            self.combined_percentage = (total_processed_score / total_max_score) * 100

    def before_insert(self, method=None):
        self.calculate_total_score()
        # self.class_rank = self.calculate_class_rank() or 0
        # self.division_rank = self.calculate_div_rank() or 0

    def before_submit(self, method=None):
        self.calculate_total_score()
        self.class_rank = self.calculate_class_rank() or 0
        self.division_rank = self.calculate_div_rank() or 0
        self.results = []

    def validate(self):
        self.results = []


def get_all_plans(assessment_group_res_doc):

    plans = frappe.db.get_all(
        "Assessment Plan",
        filters={
            "assessment_group": assessment_group_res_doc.get("assessment_group"),
        },
    )
    plans = [plan.get("name") for plan in plans]
    return plans


def get_all_results(assessment_group_res_doc, plans=[]):
    ar_qb = frappe.qb.DocType("Assessment Result")
    student = assessment_group_res_doc.get("student")
    assess_group = assessment_group_res_doc.get("assessment_group")
    if not student or not assess_group:
        return []

    query = (
        frappe.qb.from_(ar_qb)
        .where(
            (ar_qb.assessment_group == assess_group)
            & (ar_qb.assessment_plan.isin(plans))
            & (ar_qb.student == student)
            & (ar_qb.docstatus.isin([0, 1]))
        )
        .select(
            ar_qb.name.as_("assessment_result"),
            ar_qb.custom_total_processed_score.as_("total_score"),
            ar_qb.custom_processed_grade.as_("total_grade"),
            ar_qb.custom_scoring_type.as_("scoring_type"),
            ar_qb.maximum_score,
            ar_qb.custom_processed_percentage.as_("percentage"),
        )
    )
    return query.run(as_dict=True)
