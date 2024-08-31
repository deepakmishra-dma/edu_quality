import frappe
from erpnext.crm.doctype.lead.lead import Lead
from edu_quality.public.py.utils import add_indian_country_code


class CustomLead(Lead):
    def before_insert(self, method=None):
        contacts = frappe.db.get_list(
            "Contact",
            {"whatsapp_id": add_indian_country_code(self.fathers_phone)},
            limit_page_length=1,
            order_by="creation desc",
            ignore_permissions=True,
        )

        if len(contacts):
            self.contact_doc = frappe.get_doc(
                "Contact", contacts[0], ignore_permissions=True
            )
        else:
            self.contact_doc = self.create_contact()
        self.custom_contact_link = self.contact_doc.get("name")
        self.contact_doc.flags.ignore_permissions = True

    def after_insert(self, method=None):
        if not self.contact_doc:
            return
        self.contact_doc.whatsapp_id = add_indian_country_code(self.fathers_phone)
        if len(self.contact_doc.phone_nos) == 0:
            if self.fathers_phone:
                self.contact_doc.append(
                    "phone_nos",
                    {
                        "phone": self.fathers_phone,
                        "is_primary_mobile_no": 1,
                    },
                )
        if len(self.contact_doc.email_ids) == 0:
            if self.fathers_email:
                self.contact_doc.append(
                    "email_ids",
                    {
                        "email_id": self.fathers_email,
                        "is_primary": 1,
                    },
                )
        self.link_to_contact()
        self.contact_doc.save(ignore_permissions=True)

        if self.get("fathers_email"):
            content = enqueue_email(self)
            if content:
                add_email_activity(self, content)


def enqueue_email(doc):
    try:
        email = doc.get("fathers_email")
        program = doc.get("class")
        template_name = frappe.db.get_value("Program", program, "custom_email_template")
        email_template = frappe.get_doc("Email Template", template_name)

        content = frappe.render_template(
            email_template.get("response_html") or email_template.get("response"), {}
        )
        send_unsubscribe_message = frappe.get_value(
            "Email Account", {"default_outgoing": 1}, "send_unsubscribe_message"
        )
        email_args = {
            "recipients": [email],
            "subject": email_template.get("subject"),
            "message": content,
            "reference_doctype": doc.get("doctype"),
            "reference_name": doc.get("name"),
            "add_unsubscribe_link": send_unsubscribe_message,
            "unsubscribe_message": frappe._("Click Here"),
            "delayed": False,
        }

        frappe.sendmail(**email_args)
        return content
    except Exception as e:
        frappe.log_error("Error sending lead generation email", str(e))
        return None


def add_email_activity(doc, content):
    frappe.get_doc(
        {
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "subject": "Lead Generation",
            "content": content,
            "sent_or_received": "Sent",
            "sender": frappe.session.user,
            "recipients": doc.get("fathers_email"),
            "reference_doctype": "Lead",
            "reference_name": doc.get("name"),
        }
    ).insert(ignore_permissions=True)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def walk_in_attended_by_query(doctype, txt, searchfield, start, page_len, filters):
    user_table = frappe.qb.DocType("User")
    user_perm_table = frappe.qb.DocType("User Permission")
    query = (
        frappe.qb.from_(user_table)
        .left_join(user_perm_table)
        .on(user_table.name == user_perm_table.user)
        .where(
            (user_table.role_profile_name == "Councellor")
            & (
                (
                    (user_perm_table.allow.isnull())
                    & (user_perm_table.for_value.isnull())
                )
                | (
                    (user_perm_table.allow == "School")
                    & (user_perm_table.for_value == filters.get("school", None))
                )
            )
        )
        .select(user_table.email)
    )
    data = query.run()
    return data
