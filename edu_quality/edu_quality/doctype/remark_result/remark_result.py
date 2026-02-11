# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RemarkResult(Document):
    def before_validate(self, method=None):
        group = self.get("assessment_group")
        group_doc = frappe.get_doc("Assessment Group", group)
        template = group_doc.custom_remarks_template_id
        gender = frappe.db.get_value("Student", {"name": self.student}, "gender")
        remarks = frappe.db.get_all(
            "Assessment Remarks Scoring",
            filters={"parent": template, "parenttype": "Assessment Remarks Template"},
            fields=["*"],
        )

        remarks_hash = {gen_key(remark): remark.get("remark") for remark in remarks}
        print(remarks_hash)
        for remark in self.remarks:
            payload = {
                "feature": remark.remark,
                "gender": gender,
                "score": remark.score,
            }
            if gen_key(payload) in remarks_hash:
                remark.scored_remark = remarks_hash[gen_key(payload)]


def gen_key(remark):
    return f"{remark.get('feature')}-{remark.get('gender')}-{remark.get('score')}"
