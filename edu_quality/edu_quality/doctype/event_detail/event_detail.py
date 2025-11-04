# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import cstr
from frappe.model.document import Document
from frappe.utils import nowdate, add_days, getdate

class EventDetail(Document):

    def autoname(self):
        prefix = frappe.get_value("School", self.school, "prefix")
        starts_on = str(getdate(self.event_starts_on))
        self.name = f"{self.event_name} - ({starts_on}) - {prefix}"

    def before_save(self):
        self.update_classes()

    def update_classes(self):
        event = frappe.get_doc("Event", self.event)
        # Get the existing classes
        existing_classes = frappe.db.get_all(
            "Classes", filters={"parent": self.name}, pluck="class"
        )
        # Remove classes that are no longer applicable
        self.classes_applicable_to = []

        # Add new applicable classes
        for cls in event.custom_classes:
            class_name = cls.get("class")
            if class_name not in existing_classes:
                self.append("classes_applicable_to", {"class": class_name})

    @frappe.whitelist()
    def get_students(self, args):
        refno = args.get("reference_number")
        student_status = args.get("student_status")
        students = []
        if refno:
            school = args.get("school")
            refno_list = refno.split(",")
            students = frappe.get_all(
                "Student",
                filters={
                    "reference_number": ["in", refno_list],
                    "school": school,
                    "student_status": student_status,
                },
                fields=["name", "student_name"],
            )
            print(students, school, refno_list)
        return students

    @frappe.whitelist()
    def send_registration_link(self, data):
        data = frappe.parse_json(data)
        base_url = frappe.utils.get_url() + "/event-registration-form/"
        for d in data:
            registration_url = base_url + d.get("name")
            student = frappe.get_doc("Student", d.get("student"))
            frappe.sendmail(
                recipients=student.student_email_id,
                subject="Registration Link",
                message=f"Click on the link to register for the event: {registration_url}",
            )
        return True

    def validate_students(self):
        if isinstance(self.student_status, str):
            statuses = [status.strip() for status in self.student_status.split(",")]
        else:
            statuses = []
        students = self.winning_students + self.participating_students

        for student in students:
            school = frappe.get_value("Student", student.student, "school")
            if school != self.school:
                frappe.throw(
                    f"Student {student.student_name}({student.student}) does not belong to the school {self.school}"
                )

            student_status = frappe.get_value(
                "Student", student.student, "student_status"
            )
            if statuses and student_status not in statuses:
                frappe.throw(
                    f"Student {student.student_name}({student.student}) status must be one of {self.student_status}"
                )

    def _validate_selects(self):
        if frappe.flags.in_import:
            self.validate_students()
            return

        for df in self.meta.get_select_fields():
            if (
                df.fieldname == "naming_series"
                or not self.get(df.fieldname)
                or not df.options
            ):
                continue

            options = (df.options or "").split("\n")

            # if only empty options
            if not filter(None, options):
                continue

            # strip and set
            self.set(df.fieldname, cstr(self.get(df.fieldname)).strip())
            value = self.get(df.fieldname)

            if value not in options and not (
                frappe.flags.in_test and value.startswith("_T-")
            ):
                # show an elaborate message
                prefix = (
                    _("Row #{0}:").format(self.idx) if self.get("parentfield") else ""
                )
                label = _(self.meta.get_label(df.fieldname))
                comma_options = '", "'.join(_(each) for each in options)

                frappe.throw(
                    _('{0} {1} cannot be "{2}". It should be one of "{3}"').format(
                        prefix, label, value, comma_options
                    )
                )

    def remind(self):
        """
        Send reminders for the event based on the settings
        """
        try:
            from nextai.funnel.custom_trigger import trigger_event

            mgr_settings = frappe.get_single("MGR Settings")
            today_date = getdate(nowdate())

            # Send reminders for registration
            if mgr_settings.send_reminder_for_registration:
                reminder_date = calculate_reminder_date(
                    self.last_date, mgr_settings.registration_before_days
                )
                if reminder_date and today_date >= reminder_date:
                    trigger_event(self, "send_registration_reminder")

            # Send reminders for event
            if mgr_settings.send_reminder_for_event:
                reminder_date = calculate_reminder_date(
                    self.event_starts_on, mgr_settings.event_before_days
                )
                if reminder_date and today_date >= reminder_date:
                    trigger_event(self, "send_event_reminder")

        except:
            frappe.log_error(
                "Error While Sending Reminders for Event",
                frappe.get_traceback(),
            )


def calculate_reminder_date(date_from, days_before):
    """
    Calculate the reminder date based on the date_from and days_before
    """
    if date_from:
        return getdate(add_days(date_from, -abs(days_before)))
    return None


def send_event_reminder():
    """
    Send event reminder
    """
    events = frappe.get_all("Event Detail", {"event_starts_on": [">=", nowdate()]})
    for event in events:
        event_doc = frappe.get_doc("Event Detail", event.name)
        event_doc.remind()


@frappe.whitelist()
def add_participating_students(student_data):
    student_data = frappe.parse_json(student_data)
    parent_name = student_data.get("parent")
    student = student_data.get("student")
    parent_doc = frappe.get_doc("Event Detail", parent_name)
    if not frappe.db.exists(
        "Student Data",
        {
            "student": student,
            "parent": parent_name,
            "parentfield": "participating_students",
        },
    ):
        parent_doc.append(
            "participating_students",
            {
                "student": student_data.get("student"),
                "student_name": student_data.get("student_name"),
                "refno": student_data.get("refno"),
            },
        )
        parent_doc.save()
        return True
    return False
