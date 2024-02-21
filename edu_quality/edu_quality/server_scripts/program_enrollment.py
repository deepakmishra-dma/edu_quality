import frappe 
from edu_quality.edu_quality.server_scripts.utils import is_rolled_over, class_count_before_rollover
from frappe import _

def validate_rollover(doc,method=None):
    if not is_rolled_over():
        count = class_count_before_rollover(doc)
        division = frappe.get_doc("Division",doc.student_group)

        if not count<len(division.students):
            frappe.throw(
				_("""Cannot enroll more than {0} students for this student group."""))