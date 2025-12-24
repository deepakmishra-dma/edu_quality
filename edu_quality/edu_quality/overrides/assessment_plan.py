import frappe
from education.education.doctype.assessment_plan.assessment_plan import AssessmentPlan
from edu_quality.public.py.utils import extract_year_from_academic_year_name
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
import json


class CustomAssessmentPlan(AssessmentPlan):
    def before_validate(self, method=None):
        self.assessment_name = name_func(self)
        if frappe.db.exists(
            "Assessment Plan",
            {
                "assessment_group": self.assessment_group,
                "academic_year": self.academic_year,
                "course": self.course,
                "student_group": self.student_group,
                "custom_type": self.custom_type,
                "custom_textbook": ["in", ["ALL", "All", self.custom_textbook]],
                "name": ["!=", self.name],
                "docstatus": ["in", [0, 1]],
            },
        ):
            frappe.throw(
                f"{self.custom_type} Exam for this subject,division,textbook and assessment group already exists"
            )

        check_for_duplicates(self)
        check_for_empty_scale(self)

    def autoname(self, method=None):
        self.name = name_func(self)


def check_for_empty_scale(self):
    for criteria in self.assessment_criteria:
        if criteria.get("custom_scale") == 0:
            frappe.errprint(
                f"Scale 0 is not allowed for {criteria.get('assessment_criteria')},Setting it to 1"
            )
            criteria.custom_scale = 1


@frappe.whitelist()
def name_func(assessment_plan_doc):
    assessment_plan_doc = (
        json.loads(assessment_plan_doc)
        if isinstance(assessment_plan_doc, str)
        else assessment_plan_doc
    )
    division = frappe.get_doc("Student Group", assessment_plan_doc.get("student_group"))
    program = frappe.get_doc("Program", division.get("program"))

    if (
        assessment_plan_doc.get("custom_textbook")
        and str(assessment_plan_doc.get("custom_textbook")).lower() != "all"
    ):
        textbook_short = frappe.get_doc(
            "Textbook", assessment_plan_doc.get("custom_textbook")
        ).get("short_code")
    textbook_short = "ALL"
    academic_year = extract_year_from_academic_year_name(
        assessment_plan_doc.get("academic_year") or current_academic_year()
    )
    subject = frappe.get_doc("Course", assessment_plan_doc.get("course"))
    type = "S"
    if assessment_plan_doc.get("custom_type") == "Summative":
        type = "S"
    if assessment_plan_doc.get("custom_type") == "Formative":
        type = "F"
    return f"{assessment_plan_doc.get('assessment_group')} {academic_year} {type}{subject.get('custom_short_code')}{textbook_short}{program.get('program_name')}{division.get('student_group_name')}"


def check_for_duplicates(assessment_plan_doc):
    dup_cr_hash = {}
    for criteria in assessment_plan_doc.assessment_criteria:
        criteria_name = (
            f"{criteria.get('assessment_criteria')}-{criteria.get('custom_exam_type')}"
        )
        if criteria_name not in dup_cr_hash:
            dup_cr_hash[criteria_name] = True
        elif (
            criteria_name in dup_cr_hash
            and assessment_plan_doc.custom_is_descriptive == 0
        ):
            frappe.throw(
                "Assessment Criteria with same exam type already present in  the exam/assessment plan"
            )


@frappe.whitelist()
def get_assessment_cr_textbooks():
    textbooks = frappe.db.get_all("Textbook")
    return ["ALL"] + [i.get("name") for i in textbooks]


@frappe.whitelist()
def get_questions(paper):

    exam_paper = frappe.get_doc("Descriptive Exam Paper", paper)

    create_descriptive_criteria()
    print(exam_paper.questions)
    questions = [question.question for question in exam_paper.questions]

    all_questions = frappe.db.get_all(
        "Descriptive Question",
        filters={"name": ["in", questions]},
        fields=["name", "parent_descriptive_question", "max_marks", "min_marks"],
    )

    result = []

    for question in all_questions:
        result.append(
            {
                "custom_question": question.name,
                "custom_parent_question": question.parent_descriptive_question,
                "custom_scale": 1,
                "assessment_criteria": "Descriptive Question",
                "maximum_score": question.max_marks,
            }
        )
    return result


def create_descriptive_criteria():
    if not frappe.db.exists("Assessment Criteria", "Descriptive Question"):
        doc = frappe.new_doc("Assessment Criteria")
        doc.assessment_criteria = "Descriptive Question"
        doc.insert(ignore_permissions=True)
