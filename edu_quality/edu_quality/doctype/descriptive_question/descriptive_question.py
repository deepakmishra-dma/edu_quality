# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet
from edu_quality.public.py.utils import extract_year_from_academic_year_name
from edu_quality.edu_quality.server_scripts.utils import current_academic_year


class DescriptiveQuestion(NestedSet):
    def autoname(self, method=None):
        academic_year = extract_year_from_academic_year_name(
            self.get("academic_year") or current_academic_year()
        )
        subject_short_code = self.get("subject_short_code")
        name = f"{academic_year} {subject_short_code} {self.question}"
        self.name = name
        return name
