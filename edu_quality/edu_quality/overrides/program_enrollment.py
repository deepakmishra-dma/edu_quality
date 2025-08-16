import frappe
from education.education.doctype.program_enrollment.program_enrollment import ProgramEnrollment
from frappe.utils import comma_and, get_link_to_form, getdate
from frappe import _
from frappe.utils.data import cstr

class CustomProgramEnrollment(ProgramEnrollment):
    def validate_academic_year(self):
        start_date, end_date = frappe.db.get_value(
            "Academic Year", self.academic_year, ["year_start_date", "year_end_date"]
        )
        if self.enrollment_date:
            # if start_date and getdate(self.enrollment_date) < getdate(start_date):
            #     frappe.throw(
            #         _(
            #             "Enrollment Date cannot be before the Start Date of the Academic Year {0}"
            #         ).format(get_link_to_form("Academic Year", self.academic_year))
            #     )

            if end_date and getdate(self.enrollment_date) > getdate(end_date):
                frappe.throw(
                    _("Enrollment Date cannot be after the End Date of the Academic Term {0}").format(
                        get_link_to_form("Academic Year", self.academic_year)
                    )
                )

    def validate_academic_term(self):
        start_date, end_date = frappe.db.get_value(
            "Academic Term", self.academic_term, ["term_start_date", "term_end_date"]
        )
        if self.enrollment_date:
            # if start_date and getdate(self.enrollment_date) < getdate(start_date):
            #     frappe.throw(
            #         _(
            #             "Enrollment Date cannot be before the Start Date of the Academic Term {0}"
            #         ).format(get_link_to_form("Academic Term", self.academic_term))
            #     )

            if end_date and getdate(self.enrollment_date) > getdate(end_date):
                frappe.throw(
                    _("Enrollment Date cannot be after the End Date of the Academic Term {0}").format(
                        get_link_to_form("Academic Term", self.academic_term)
                    )
                )


    def _validate_selects(self):
        if frappe.flags.in_import:
            self.update_student_data()
            self.sync_division_data()
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


    def update_student_data(self):
        division = frappe.get_value("Student Group", self.student_group, "student_group_name")
        fields = {
            'roll_no': self.roll_no,
            'tiffin_rack_no': self.tiffin_rack_no,
            'bus_service_required': self.transport_service_required,
            'school_house': self.school_house,
            'pickup_bus': self.pickup_bus,
            'drop_bus': self.drop_bus,
            'pickup_address': self.pickup_address,
            'drop_address': self.drop_address,
            'image': self.image,
            'program': self.program,
            'custom_division': division,
        }
        frappe.db.set_value("Student", self.student, fields)


    def sync_division_data(self):
        division = frappe.get_value("Student Group Student", {"student": self.student}, "parent")
        if self.student_group != division:
            self.student_group = division