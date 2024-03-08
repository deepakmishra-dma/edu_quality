import frappe 
from frappe.utils import today




def current_academic_year():
    filter = [["Academic Year","year_start_date","<=",today()],
			      ["Academic Year","year_end_date",">=",today()]]
    if frappe.db.exists("Academic Year",filter):
        return frappe.db.get_value("Academic Year",filter)
    
def next_academic_year(current=None):
    if not current:
        current = current_academic_year()
    current_end_date = frappe.db.get_value("Academic Year",current,"year_end_date")
    filters = [["Academic Year","year_start_date",">",current_end_date]]
    if frappe.db.exists("Academic Year",filters):
        return frappe.db.get_value("Academic Year",filters,order_by="year_start_date")

def previous_academic_year(current=None):
    if not current:
        current = current_academic_year()
    current_start_date = frappe.db.get_value("Academic Year",current,"year_start_date")
    filters = [["Academic Year","year_end_date","<=",current_start_date]]
    if frappe.db.exists("Academic Year",filters):
        return frappe.db.get_value("Academic Year",filters,order_by="year_end_date")
    

def is_rolled_over(academic_year=None):
    if academic_year:
        filter = academic_year
    else:
        filter = [["Academic Year","year_start_date","<=",today()],
                    ["Academic Year","year_end_date",">=",today()]]
    if frappe.db.exists("Academic Year",filter):
        return frappe.db.get_value("Academic Year",filter,order_by="year_start_date")
    

def get_previous_class(program):
    filters = [
        ["Program","school","=",program.school],
        ["Program","sequence","=",program.sequence-1]
    ]
    if frappe.db.exists("Program",filters):
        return frappe.db.get_value("Program",filters)
    
def next_class(program):
    filters = [
        ["Program","school","=",program.school],
        ["Program","sequence","=",program.sequence+1]
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


def mark_rolled_over(academic_year):
    next_academic_year = next_academic_year(academic_year)
    if next_academic_year:
        frappe.db.set_value("Academic Year",next_academic_year,"rolled_over",1)


def shift_reference_series(school):
    programs = frappe.get_all("Program",filters={"school":school},fields=["name","reference_series"],order_by="sequence")
    previous_series = ""
    for i in programs:
        if previous_series:
            frappe.db.set_value("Program",i.name,"reference_series",previous_series)
            previous_series = i.reference_series
    previous_series = chr(ord(previous_series[0])+1) + chr(ord(previous_series[1])+1)     
    for i in programs:
        frappe.db.set_value("Program",i.name,"reference_series",previous_series)
        break


def get_next_class(current_class):
    school,current_sequence = frappe.db.get_value("Program",current_class,["school","sequence"])
    if frappe.db.exists("Program",{"school":school,"sequence":current_sequence+1}):
        return frappe.db.get_value("Program",{"school":school,"sequence":current_sequence+1})
    return None


@frappe.whitelist()
def projected_strength(current_class):
    next_class = get_next_class(current_class)
    strength = frappe.db.count("Program Enrollment",{"program":current_class,'academic_year':current_academic_year()})
    if next_class:
        strength += frappe.db.count("Program Enrollment",{"program":next_class,'academic_year':next_academic_year()})
    return strength

