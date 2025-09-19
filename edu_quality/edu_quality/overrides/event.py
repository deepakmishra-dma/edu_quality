import frappe
from frappe.desk.doctype.event.event import Event


class CustomEvent(Event):
    def on_update(self):
        super().on_update()
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
        self.subject = self.subject.split("-")[0].strip()
        if self.all_classes:
            new_name = "All Classes"
        else:
            class_ids = [c.get("class") for c in self.custom_classes]
            if class_ids:
                program_names = frappe.db.get_values(
                    "Program", {"name": ["in", class_ids]}, "program_name", as_dict=True
                )
                subject = [program["program_name"] for program in program_names]
                new_name = ", ".join(subject)
            else:
                new_name = ""

        self.subject = f"{self.subject} - {new_name}" if new_name else self.subject
