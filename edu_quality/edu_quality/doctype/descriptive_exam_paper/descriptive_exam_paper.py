import frappe
from frappe.model.document import Document
import json
from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.public.py.utils import extract_year_from_academic_year_name
from frappe.model.mapper import get_mapped_doc


class DescriptiveExamPaper(Document):
    def autoname(self, method=None):
        self.name = name_func(self)

    def before_validate(self):
        if self.get("__unsaved") and self.get("__islocal") and frappe.flags.in_import:
            questions = [question.question for question in self.questions]
            result = add_question(questions)

            for question in result:
                question_name = question.get("name")
                par_ques_name = question.get("parent_descriptive_question")
                if question_name not in questions:
                    self.append(
                        "questions",
                        {"question": question_name, "parent_question": par_ques_name},
                    )


@frappe.whitelist()
def name_func(descriptive_exam_doc):
    descriptive_exam_doc = (
        json.loads(descriptive_exam_doc)
        if isinstance(descriptive_exam_doc, str)
        else descriptive_exam_doc
    )

    academic_year = extract_year_from_academic_year_name(
        descriptive_exam_doc.get("academic_year") or current_academic_year()
    )
    subject = frappe.get_doc("Course", descriptive_exam_doc.subject)
    class_type = descriptive_exam_doc.get("class_type")

    class_type_doc = frappe.get_doc("Class Type", class_type)

    return f"{descriptive_exam_doc.name1} {subject.get('custom_short_code')}{class_type_doc.short_code} {academic_year}"


# edu_quality.edu_quality.doctype.descriptive_exam_paper.descriptive_exam_paper.add_question
@frappe.whitelist()
def add_question(docnames):
    parsed_docnames = json.loads(docnames) if isinstance(docnames, str) else docnames
    res = get_all_children_of_multiple_docs("Descriptive Question", parsed_docnames)

    return res


def get_all_children(parent_doctype, parent_name, parent_descriptive_question=None):
    """Recursively fetch all child nodes of a tree document using frappe.qb."""
    ChildDoc = frappe.qb.DocType(parent_doctype)
    children = (
        frappe.qb.from_(ChildDoc)
        .select(ChildDoc.name, ChildDoc.parent_descriptive_question)
        .where(ChildDoc.parent_descriptive_question == parent_name)
        .run(as_dict=True)
    )

    all_children = [
        {"name": parent_name, "parent_question": parent_descriptive_question}
    ]  # Include the parent name in the result
    for child in children:
        all_children.append(child)
        child_children = get_all_children(
            parent_doctype, child["name"], child["parent_descriptive_question"]
        )
        all_children.extend(child_children)
    return all_children


def get_all_children_of_multiple_docs(parent_doctype, parent_names):
    """Fetch all child nodes of multiple tree documents."""
    all_children = []
    for parent_name in parent_names:
        all_children.extend(get_all_children(parent_doctype, parent_name))
    return deduplicate_dicts(all_children)


def deduplicate_dicts(dicts):
    seen = {}
    deduped_list = []

    for d in dicts:
        name = d["name"]
        if name not in seen:
            seen[name] = True
            deduped_list.append(d)

    return deduped_list
