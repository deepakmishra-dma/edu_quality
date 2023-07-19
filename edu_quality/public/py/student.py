import frappe 
from frappe.model.naming import make_autoname

def autoname(doc,method=None):
    if doc.student_applicant:
        applicant = frappe.get_doc("Student Applicant",doc.student_applicant)
        prefix = ''
        if frappe.db.exists("Prefix Table",{'school':applicant.school}):
            prefix = frappe.get_value("Prefix Table",{'school':applicant.school},'prefix')
        if frappe.db.exists("Reference Number Table",{'program':applicant.program}):
            series = frappe.get_value("Reference Number Table",{'program':applicant.program},'series')
            prefix += series
        if frappe.db.count("Student",[["name","Like","%prefix%"]])>=99:
            prefix = prefix[:-2] + chr(ord(prefix[-2]) + 1)
            series = series[0] + chr(ord(series[1])+1)
            frappe.db.set_value("Reference Number Table",{'program':applicant.program},'series',series)
        if not prefix:
            prefix = "EDU-STU-2023-"
        prefix += ".##"
        doc.name = make_autoname(prefix)