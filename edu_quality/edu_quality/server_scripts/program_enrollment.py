import frappe
from frappe import _

from edu_quality.edu_quality.server_scripts.utils import class_count_before_rollover, is_rolled_over


def validate_rollover(doc, method=None):
	if not is_rolled_over():
		count = class_count_before_rollover(doc)
		division = frappe.get_doc("Division", doc.student_group)

		if not count < len(division.students):
			frappe.throw(_("""Cannot enroll more than {0} students for this student group."""))


def on_cancel(doc, method=None):
	division = frappe.get_doc("Student Group", doc.student_group)
	to_remove = [d for d in division.students if d.student == doc.student]
	for d in to_remove:
		division.remove(d)
	division.save()
