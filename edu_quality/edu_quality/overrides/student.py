import frappe
from education.education.doctype.student.student import Student
from frappe.auth import LoginManager
from edu_quality.edu_quality.server_scripts.guardian import set_guardian_permissions
from frappe.utils import getdate
import datetime
from erpnext.accounts.doctype.payment_request.payment_request import get_gateway_details
from erpnext.accounts.party import get_party_bank_account
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)


class CustomStudent(Student):
    def autoname(self):
        school_prefixes = {
            "Walnut School at Fursungi": "FU",
            "Walnut School at Shivane": "SH",
            "Walnut School at Wakad": "WA",
        }

        if self.imported and self.reference_number:
            prefix = school_prefixes.get(self.school, "")
            doc_name = prefix + self.reference_number
            self.name = doc_name
        elif self.reference_number:
            prefix = school_prefixes.get(self.school, "")
            doc_name = prefix + self.reference_number
            self.name = doc_name
        elif self.student_applicant:
            applicant = frappe.get_doc("Student Applicant", self.student_applicant)
            prefix = frappe.get_value("School", applicant.school, "prefix")
            series = self.get_reference()
            prefix += series
            ref_id = self.get_last_id(prefix)
            if ref_id == "max":
                prefix = prefix[:2]
                if series[1] != "Z":
                    series = series[0] + chr(ord(series[1]) + 1)
                elif series[0] != "Z":
                    series = chr(ord(series[0]) + 1) + "A"
                else:
                    series = "A" + "A"
                frappe.db.set_value(
                    "Program", applicant.program, "reference_series", series
                )
                prefix = prefix + series + "01"
            else:
                prefix = prefix + ref_id
            self.name = prefix
            self.student_email_id = self.name + "@walnutedu.in"
            self.reference_number = self.name[2:]
    
    def get_reference(self):
        if not frappe.db.get_value(
            "Academic Year",
            {"custom_current_academic_year": 1},
            "rolled_over",
        ):
            current_program = frappe.get_doc("Program", self.program)
            series = frappe.db.get_value(
                "Program",
                {
                    "school": current_program.school,
                    "sequence": current_program.sequence - 1,
                },
                "reference_series",
            )
            if not series:
                series = current_program.reference_series
                series = chr(ord(series[0]) + 1) + series[1]
        else:
            series = frappe.db.get_value("Program", self.program, "reference_series")
        return series


    def get_last_id(self,prefix):
        val = frappe.db.get_all(
            "Student", [["name", "Like", prefix + "%"]], "name", order_by="name"
        )
        if val:
            series = int(val[-1].name[-2:])
            if series == 99:
                return "max"
            series += 1
            return str(series) if series > 9 else "0" + str(series)
        else:
            return "01"


    def validate_user(self):
        current_user = frappe.session.user 
        login_manager = LoginManager()
        login_manager.login_as("Administrator")
        if not frappe.db.get_single_value(
            "Education Settings", "user_creation_skip"
        ) and not frappe.db.exists("User", self.student_email_id):
            student_user = frappe.get_doc(
                {
                    "doctype": "User",
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "email": self.student_email_id,
                    "gender": self.gender,
                    "send_welcome_email": 0,
                    "user_type": "Website User",
                }
            )
            student_user.add_roles("Student")
            student_user.save(ignore_permissions=True)

            self.user = student_user.name
        login_manager.login_as(current_user)


    def on_update(self):
        # Giving permissions to guardian
        set_guardian_permissions(self)

    @frappe.whitelist()
    def validate_bank_account(self):
        return frappe.db.exists("Bank Account", {"party": self.name})


    @frappe.whitelist()
    def cancel_student(self,academic_year,fee_collection):
        try:
            student = self.name
            if frappe.db.exists("Program Enrollment",{'student':student,'academic_year':academic_year,'docstatus':1}):
                frappe.db.set_value("Program Enrollment",{'student':student,'academic_year':academic_year,'docstatus':1},'docstatus',2)
            frappe.db.set_value("Student",student,'enabled',0)
            frappe.db.set_value("Student",student,"student_status","Cancelled")
            if fee_collection == "Deposit Refund":
                return self.check_deposit()
            elif fee_collection == "Ignore Pending Fee":
                self.check_deposit()
                return self.reverse_pending_fees(academic_year)
        except Exception as e:
            frappe.logger("Cancel").exception(e)
            frappe.throw(e)

    def reverse_pending_fees(self,academic_year):
        fees_list = frappe.db.get_all("Fees",filters=[["Fees","docstatus","=","1"],["Fees","student","=",self.name],["Fees","outstanding_amount",">",0],["Fees","academic_year","=",academic_year]])
        for fee in fees_list:
            fee_doc = frappe.get_doc("Fees",fee.name)
            if fee_doc.outstanding_amount == fee_doc.grand_total:
                pr_list = frappe.db.get_all("Payment Request",{'reference_name':fee.name,'docstatus':1})
                for pr in pr_list:
                    pr_doc = frappe.get_doc("Payment Request",pr.name)
                    pr_doc.cancel()
                fee_doc.cancel()
                return 1
            else:
                return fee_doc.reverse_pending_fees()

    def check_deposit(self):
        fees_list = frappe.db.get_all("Fees",filters={'docstatus':1,'student':self.name})
        for fee in fees_list:
            if frappe.db.exists("Fee Component",[['parent','=',fee.name],['fees_category','like','%DEPOSIT%']]):
                deposit,account = frappe.db.get_value("Fee Component",[['parent','=',fee.name],['fees_category','like','%DEPOSIT%']],['amount','label'])
                deposit_paid = 0
                if frappe.db.exists("Payment Request",[["Payment Request","reference_name","=",fee.name],["Payment Request","payment_term","is","not set"],["Payment Request","status","=","Paid"]]):
                    deposit_paid = 1
                description,outstanding = frappe.db.get_value("Payment Schedule",{'parent':fee.name,"payment_term":"Term 1"},['description','outstanding'])
                if "deposit" in description.lower() and outstanding==0:
                        deposit_paid=1
                if deposit_paid:
                    return self.refund_deposit(fee.name,deposit,account)
                return frappe.throw("Deposit Not Paid!")
        return 1

    def refund_deposit(self,fee,amount,account):
        student = self.name
        gateway_account = get_gateway_details({}) or frappe._dict()
        pr = frappe.new_doc("Payment Request")
        ref_doc = frappe.get_doc("Fees",fee)
        pr.update(
            {
                "payment_gateway_account": gateway_account.get("name"),
                "payment_gateway": gateway_account.get("payment_gateway"),
                "payment_account": gateway_account.get("payment_account"),
                "payment_channel": gateway_account.get("payment_channel"),
                "payment_request_type": "Outward",
                "currency": "INR",
                "grand_total": amount,
                "email_to": student+"@walnutedu.in",
                "subject": "Deposit Refund For for {0}".format(student),
                "message": "Deposit Refund",
                "reference_doctype": "Fees",
                "reference_name": fee,
                "party_type": "Student",
                "party": student,
                "bank_account": account,
                "company": ref_doc.get("company"),
            }
        )

        # Update dimensions
        pr.update(
            {
                "cost_center": ref_doc.get("cost_center"),
                "project": ref_doc.get("project"),
            }
        )

        for dimension in get_accounting_dimensions():
            pr.update({dimension: ref_doc.get(dimension)})

        pr.insert(ignore_permissions=True)
        pr.submit()
        #add deposit refund in student ledger
        return 1

    @frappe.whitelist()
    def mark_entry(self, status, reason=None, date=None, time=None):
        student = self.name
        if not date:
            date = getdate()
        if not time:
            time = datetime.datetime.now().strftime("%H:%M:%S")

        try:
            if frappe.db.exists("Attendance Entry", {"student": student, "date": date}):
                entry = frappe.get_doc(
                    "Attendance Entry", {"student": student, "date": date}
                )
                entry.append(
                    "absent_and_delays",
                    {
                        "reason": reason,
                        "status": status,
                        "timestamp": date + " " + time,
                        "user": frappe.session.user,
                    },
                )
                entry.flags.ignore_mandatory = True
                entry.save(ignore_permissions=True)
            else:
                entry = frappe.new_doc("Attendance Entry")
                entry.student = student
                entry.date = date
                entry.append(
                    "absent_and_delays",
                    {
                        "reason": reason,
                        "status": status,
                        "timestamp": date + " " + time,
                        "user": frappe.session.user,
                    },
                )
                entry.insert(ignore_permissions=True)
            return True
        except Exception as e:
            frappe.logger("entry").exception(e)
            return False
