import frappe
from edu_quality.public.py.utils import (
    add_indian_country_code,
    remove_indian_country_code
)

def before_validate(self, method=None):
    if frappe.db.exists('Contact',{"whatsapp_id":add_indian_country_code(self.whatsapp_id)}):
        frappe.throw("Contact Already Exists Skipping Creation")
        return
    phone_no = remove_indian_country_code(self.whatsapp_id)
    self.contact_doc.append(
            "phone_nos",
            {
                "phone": phone_no,
                "is_primary_mobile_no": 1,
            },
        )
    self.whatsapp_id = add_indian_country_code(self.whatsapp_id)
