import frappe
from frappe.desk.doctype.event.event import Event

class CustomEvent(Event):
    def on_update(self):
        super().on_update()
        self.update_subject()
        if self.all_classes:
            self.append_all_classes()

    
    def append_all_classes(self):
        """
        this method appends all classes to the event if the all_classes field is checked
        """
        classes = frappe.get_all("Program", filters={"school": self.custom_branch}, fields=["name", "school"])
        self.custom_classes = []
        for c in classes:
            self.append("custom_classes", {
                "class": c.name,
                "school": c.school
            })
    
    def update_subject(self):
        """
        this method appends the class to the subject of the event
        """
        subject = [self.subject.split(",")[0], ",\n"]
        if self.custom_classes:
            for c in self.custom_classes:
                subject.append(c.get("class"))
                subject.append(", ")

        self.subject = "".join(subject)