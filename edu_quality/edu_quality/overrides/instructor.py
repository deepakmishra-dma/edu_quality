import frappe
from education.education.doctype.instructor.instructor import Instructor


class CustomInstructor(Instructor):
	def before_save(self):
		if self.custom_teacher_alias:
			for i in self.custom_teacher_alias:
				alias = frappe.get_all(
					"Teacher Alias Group", filters={"alias": i.alias}, fields=["name", "alias", "parent"]
				)
				if len(alias) > 0:
					for i in alias:
						instructor_doc = frappe.get_doc("Instructor", i.get("parent"))
						if (
							instructor_doc.get("status") == "Active"
							and self.custom_school == instructor_doc.get("custom_school")
							and self.name != instructor_doc.name
						):
							frappe.throw(
								"Alias <b>{}</b> is Already Mapped to Teacher <b>{}</b>".format(
									i.get("alias"), i.get("parent")
								)
							)
