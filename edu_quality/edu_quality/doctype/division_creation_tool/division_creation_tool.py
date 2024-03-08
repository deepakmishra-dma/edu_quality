# Copyright (c) 2023, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from education.education.doctype.student_group.student_group import \
    get_students
from frappe import _
from frappe.utils import nowdate,today
from edu_quality.edu_quality.server_scripts.utils import current_academic_year,next_academic_year

class DivisionCreationTool(Document):
	@frappe.whitelist()
	def get_current_academic_year(self):
		return current_academic_year()
		
	@frappe.whitelist()
	def get_next_academic_year(self):
		return next_academic_year()
		

	@frappe.whitelist()
	def get_courses(self):
		group_list = []
		self.get_existing_groups()
		for group in self.existing_groups:
			next_class = self.next_class(group.sequence)
			if next_class:
				next_batch = self.get_batch(next_class,group.student_group_name)
			if group.program == self.first_class or group.program==self.last_class: # eg: If kg, add KG and 1st
				if group.program == self.last_class:
					continue
				group_list.append({
					"group_based_on": "Batch",
					"batch": group.batch,
					"student_group_name": group.student_group_name,
					"program": group.program,
					"max_strength": group.max_strength
				})
			group_list.append({
				"group_based_on": "Batch",
				"batch": next_batch or group.batch,
				"student_group_name": group.student_group_name,
				"program": next_class,
				"max_strength": group.max_strength
			})


		return group_list
	
	def next_class(self,sequence):
		if frappe.db.exists("Program",{'school': self.school,'sequence':sequence+1}):
			return frappe.db.get_value("Program",{'school': self.school,'sequence':sequence+1})
		return None
	
	def get_batch(self,program,student_group_name):
		if frappe.db.exists("Student Group",{'program':program,
									   'student_group_name':student_group_name,
									   'academic_year':self.academic_year}):
			return frappe.get_value("Student Group",{'program':program,
											'student_group_name':student_group_name,
									   		'academic_year':self.academic_year},'batch')
		return None


	
	def get_existing_groups(self):
		if not self.academic_year:
			self.academic_year = self.get_current_academic_year()
		self.existing_groups = frappe.db.sql("""
								select sg.student_group_name, sg.max_strength, sg.batch, sg.program,p.sequence
								from `tabStudent Group` as sg 
								left join `tabProgram` as p on sg.program=p.name
								where sg.academic_year='%s' and sg.custom_school='%s'
								order by p.sequence, sg.student_group_name
								  """ %(self.academic_year,self.school), as_dict=1)
		if len(self.existing_groups):
			self.first_class = self.existing_groups[0]['program']
			self.last_class = self.existing_groups[-1]['program']

	@frappe.whitelist()
	def create_student_groups(self):
		if not self.next_academic_year:
			self.next_academic_year = self.get_next_academic_year()
		if not self.courses:
			frappe.throw(_("""No Student Groups created."""))

		l = len(self.courses)
		for d in self.courses:
			if not d.student_group_name:
				frappe.throw(_("Student Group Name is mandatory in row {0}").format(d.idx))

			if d.group_based_on == "Course" and not d.course:
				frappe.throw(_("Course is mandatory in row {0}").format(d.idx))

			if d.group_based_on == "Batch" and not d.batch:
				frappe.throw(_("Batch is mandatory in row {0}").format(d.idx))

			frappe.publish_realtime(
				"student_group_creation_progress",
				{"progress": [d.idx, l]},
				user=frappe.session.user,
			)

			student_group = frappe.new_doc("Student Group")
			student_group.student_group_name = d.student_group_name
			student_group.group_based_on = d.group_based_on
			student_group.program = d.program
			student_group.course = d.course
			student_group.batch = d.batch
			student_group.max_strength = d.max_strength
			student_group.academic_year = self.next_academic_year
			student_group.save()

		frappe.msgprint(_("{0} Student Groups created.").format(l))

