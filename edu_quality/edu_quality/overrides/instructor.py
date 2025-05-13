import frappe
from education.education.doctype.instructor.instructor import Instructor
class CustomInstructor(Instructor):
    def before_save(self):
        if self.custom_teacher_alias:
           for i in self.custom_teacher_alias:
               alias = frappe.get_all('Teacher Alias Group',filters={'alias':i.alias},fields=['name','alias','parent'])
               if len(alias)>0:
                   frappe.throw('Alias <b>{}</b> is Already Mapped to Teacher <b>{}</b>'.format(alias[0].get('alias'),alias[0].get('parent')))
            