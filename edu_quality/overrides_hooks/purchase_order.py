from edu_quality.public.py.utils import im_2_b64, gen_qr_code_b64
import frappe


def before_validate(self, method=None):
    frappe.errprint("updating")
    self.custom_qr_code_base = gen_qr_code_b64(self.name)
