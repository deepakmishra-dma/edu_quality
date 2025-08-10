import frappe
from education.education.doctype.assessment_plan.assessment_plan import AssessmentPlan


class CustomAssessmentPlan(AssessmentPlan):
    def before_validate(self, method=None):
        # docs = frappe.get_all("")
        # self.assessment_criteria

        pass


# def
