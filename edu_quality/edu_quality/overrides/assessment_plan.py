import frappe
from frappe import _
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
                "custom_is_descriptive": self.custom_is_descriptive,
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

    def validate(self, method=None):
        self.validate_overlap()
        if not self.custom_is_descriptive:
            self.validate_max_score()
            self.validate_assessment_criteria()

    def validate_max_score(self):
        max_score = 0
        for d in self.assessment_criteria:
            max_score += d.maximum_score

        if self.maximum_assessment_score != max_score:
            frappe.throw(
                _("Sum of Scores of Assessment Criteria needs to be {0}.").format(
                    self.maximum_assessment_score
                )
            )

    def autoname(self, method=None):
        self.name = name_func(self)

    def after_insert(self, method=None):
        frappe.enqueue(
            on_amend,
            self=self,
            queue="long",
            timeout=600,
        )


def on_amend(self):
    if not self.amended_from:
        return

    old_results = frappe.get_all(
        "Assessment Result",
        {"assessment_plan": self.amended_from, "docstatus": ["in", [0, 1]]},
        ["name"],
    )

    if not old_results:
        return
    total = len(old_results)
    processed = 0

    def update_progress():
        frappe.publish_progress(
            processed / total * 100, title="Recreating Assessment Results"
        )

    for result in old_results:
        res_doc = frappe.get_doc("Assessment Result", result.get("name"))
        new_doc = frappe.copy_doc(res_doc)
        new_doc.amended_from = None
        new_doc.assessment_plan = self.name
        new_doc.maximum_score = self.maximum_assessment_score
        combine_new_plan_cr_results(self, new_doc)
        new_doc.save()

        processed += 1
        update_progress()


def combine_new_plan_cr_results(self, new_doc):
    cr = {}
    visited = {}
    for cr in self.assessment_criteria:
        cr[gen_field(cr, self.custom_is_descriptive)] = cr

    for de in new_doc.details:
        cr_field = gen_field(de, self.custom_is_descriptive)
        cr_data = cr[cr_field]
        visited = {cr_field}
        if cr_data:
            de.maximum_score = cr_data.get("maximum_score")
            de.custom_scale = cr_data.get("custom_scale")
            de.custom_allow_revaluation = cr_data.get("custom_allow_revaluation")

    for cr_key in cr:
        if cr_key not in visited:
            cr_data = cr[cr_key]
            new_doc.append("details", cr_data)


def gen_field(data, is_descriptive):
    if not is_descriptive:
        return data.get("asessment_criteria")
    return f"{data.get('custom_question')} {data.get('assessment_criteria')}"


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
    extra = ""

    if assessment_plan_doc.get("custom_is_remark"):
        extra += "REM"
    if assessment_plan_doc.get("custom_is_descriptive"):
        extra += "DE"

    subject = frappe.get_doc("Course", assessment_plan_doc.get("course"))
    type = "S"
    if assessment_plan_doc.get("custom_type") == "Summative":
        type = "S"
    if assessment_plan_doc.get("custom_type") == "Formative":
        type = "F"
    return f"{assessment_plan_doc.get('assessment_group')} {academic_year} {type}{subject.get('custom_short_code')}{textbook_short}{program.get('program_name')}{division.get('student_group_name')}{f' {extra}' if extra else ''}"


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

    check_and_create_criteria("Descriptive Question")

    questions = [
        question.question for question in exam_paper.questions if question.selected
    ]
    question_order_hash = {
        question.question: question.order
        for question in exam_paper.questions
        if question.selected
    }
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
                "custom_is_question": 1,
                "custom_order": question_order_hash.get(question.name, 0),
            }
        )
    return result


@frappe.whitelist()
def get_remarks(template):
    """Load `remarks` from the database"""

    if not template:
        return []

    check_and_create_criteria("Remark")

    remarks = frappe.get_all(
        "Assessment Remarks Scoring",
        filters={
            "parent": template,
            "parenttype": "Assessment Remarks Template",
        },
        fields=["feature"],
    )
    result = []

    for remark in remarks:
        result.append(
            {
                "remark": remark.get("feature"),
                "custom_scale": 1,
                "assessment_criteria": "Remark",
                "custom_is_remark": 1,
                "maximum_score": 0,
            }
        )
    return result


def check_and_create_criteria(criteria):
    if not frappe.db.exists("Assessment Criteria", criteria):
        doc = frappe.new_doc("Assessment Criteria")
        doc.assessment_criteria = criteria
        doc.insert(ignore_permissions=True)
