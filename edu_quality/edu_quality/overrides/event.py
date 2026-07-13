import frappe
from frappe.desk.doctype.event.event import Event


class CustomEvent(Event):
	def before_save(self):
		super().before_save()
		self.append_classes()
		self.update_subject()

	def append_classes(self):
		"""
		this method appends all classes to the event if the all_classes field is checked
		"""
		if self.all_classes:
			classes = frappe.get_all(
				"Program",
				filters={"school": self.custom_branch},
				fields=["name", "school"],
			)
			self.custom_classes = []
			for c in classes:
				self.append("custom_classes", {"class": c.name, "school": c.school})

	def update_subject(self):
		"""
		This method appends the class to the subject of the event.
		"""
		# Fetch school prefix
		school_prefix = frappe.get_value("School", self.custom_branch, "prefix")

		# Remove the school prefix from the subject if it starts with it
		if school_prefix and self.subject.startswith(school_prefix):
			self.subject = self.subject.replace(f"{school_prefix} - ", "", 1)

		# Get the base of the subject before the last dash
		last_dash_index = self.subject.rfind("-")
		subject_base = (
			self.subject[:last_dash_index].strip() if last_dash_index != -1 else self.subject.strip()
		)

		# Determine the new name based on class information
		if self.all_classes:
			new_name = "All Classes"
		else:
			class_ids = [c.get("class") for c in self.custom_classes if c.get("class")]
			if class_ids:
				program_names = frappe.db.get_values(
					"Program", {"name": ["in", class_ids]}, ["program_name", "sequence"], as_dict=True
				)
				sorted_programs = sorted(program_names, key=lambda p: p["sequence"])
				new_name = ", ".join(p["program_name"] for p in sorted_programs)
			else:
				new_name = ""

		# Prepend school prefix to the subject base if available
		if school_prefix and not subject_base.startswith(school_prefix):
			subject_base = f"{school_prefix} - {subject_base}"

		# Update the subject
		self.subject = f"{subject_base} - {new_name}" if new_name else subject_base
