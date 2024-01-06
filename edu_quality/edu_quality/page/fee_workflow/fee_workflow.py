import frappe
import json
from frappe.model.mapper import get_mapped_doc

# edu_quality.edu_quality.page.fee_workflow.fee_workflow.create_fee_workflow
@frappe.whitelist()
def create_fee_workflow(**kwargs):
    data = json.loads(kwargs.get("data"))
    fee_structure = create_fee_structure(data)
    fee_schedule = create_fee_schedule(fee_structure,data)



def create_fee_structure(data):
    try:
        doc = frappe.new_doc("Fee Structure")
        doc.program = data.get("program")
        doc.academic_year = data.get("academicYear")
        doc.academic_term = data.get("academicTerm")
        doc.student_category = data.get("studentCategory")
        doc.school = data.get("school")
        doc.institution = data.get("institution")
        for item in data.get("editGrid"):
            doc.append("components",{
                    "fees_category" : item.get("feesCategory"), 
                    "description" : item.get("description"),
                    "amount" : item.get("amount"),
                    "fee_type" : item.get("feeType")
            })
        doc.save()
        doc.submit()
        return doc.name
    except Exception as e:
        frappe.logger("walnut").exception(e)
        frappe.throw("+++")
    
def create_fee_schedule(fee_structure,data):
    try:
        fee_schedule_doc = get_mapped_doc(
                    "Fee Structure",
                    fee_structure,
                    {"Fee Structure": {"doctype": "Fee Schedule", "field_map": {"name": "Fee Structure"}}},
                )
        fee_schedule_doc.due_date = "2023-07-12'"
        for item in data.get("studentGroup"):
            fee_schedule_doc.append("student_groups",{
                "student_group" : item.get("studentGroup"),
                "total_students" : item.get("totalStudents")
            })
        fee_schedule_doc.fee_structure = fee_structure
        fee_schedule_doc.save()
        fee_schedule_doc.submit()
        fee_schedule_doc.create_fees()
        return fee_schedule_doc.name
    except Exception as e:
        frappe.logger("walnut").exception(e)
        frappe.throw("+++")

