import frappe 
from frappe.utils import today


def is_rolled_over():
    filter = [["Academic Year","year_start_date","<=",today()],
			      ["Academic Year","year_end_date",">=",today()]]
    if frappe.db.exists("Academic Year",filter):
        return frappe.db.get_value("Academic Year",filter,"rolled_over")
    

def previous_academic_year():
    filter = [["Academic Year","year_end_date","<=",today()]]
    if frappe.db.exists("Academic Year",filter):
        return frappe.db.get_value("Academic Year",filter,order_by="year_start_date")
    

def get_previous_class(program):
    filters = [
        ["Program","school","=",program.school],
        ["Program","sequence","=",program.sequence-1]
    ]
    if frappe.db.exists("Program",filters):
        return frappe.db.get_value("Program",filters)
    
def get_division(group_name,academic_year,program):
    filters = [
        ["Division","student_group_name","=",group_name],
        ["Division","academic_year","=",academic_year],
        ["Division","program","=",program],
    ]
    if frappe.db.exists("Division",filters):
        return frappe.db.get_value("Division",filters)
    
def class_count_before_rollover(program_enrollment):
    previous_class = get_previous_class(program_enrollment.program)
    division_name = frappe.db.get_value("Division",program_enrollment.student_group,"student_group_name")
    division = get_division(division_name,previous_academic_year(),program_enrollment.program)
    filters = [
        ["Program Enrollment", "program","=",program_enrollment.program],
        ["Program Enrollment", "academic_year","=",previous_academic_year()],
        ["Program Enrollment", "program","=",program_enrollment.program],
        ["Program Enrollment", "student_group","=",division],
    ]
