# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CompositeAssessmentResult(Document):
	pass


def process_exams(acad_year, school, exam_name, program, div=[], reference_numbers=""):
	assess_plan_qb = frappe.qb.DocType("Assessment Plan")

	assess_plan_cr_qb = frappe.qb.DocType("Assessment Plan Criteria")
	div_query = assess_plan_qb.div.notnull()
	if div:
		div_query = assess_plan_qb.isin(div)
	valid_plans = (
		frappe.qb.from_(assess_plan_qb)
		.inner_join(assess_plan_cr_qb)
		.on(assess_plan_cr_qb.parent == assess_plan_qb.name)
		.where(
			(assess_plan_qb.academic_year == acad_year)
			& (assess_plan_qb.school == school)
			& (assess_plan_qb.assessment_group == exam_name)
			& (div_query)
		)
		.select(
			assess_plan_qb.name,
			assess_plan_cr_qb.custom_scale,
			assess_plan_qb.assessment_criteria,
		)
	)

	plan_hash = gen_assess_cr_hash(valid_plans.run(as_dict=True))
	assess_result_qb = frappe.qb.DocType("Assessment Result")


def gen_assess_cr_hash(assess_plans):
	plan_hash = {}
	for plan in assess_plans:
		name = plan.get("name")
		if name not in plan_hash:
			plan_hash[name] = [plan]
		else:
			plan_hash[name].append(plan)


# return plan_hash
def calculate_exam_marks():
	pass
