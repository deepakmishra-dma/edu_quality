import frappe

data = [

 {
  "custom_mgr_id": "74",
  "description": None,
  "docstatus": 0,
  "doctype": "School",
  "institution": None,
  "location": "Wakad",
  "modified": "2023-10-03 18:13:42.700013",
  "name": "Walnut School at Wakad",
  "prefix": "WA",
  "school": "Walnut School at Wakad"
 },
 {
    "custom_mgr_id": "46",
    "description": None,
    "docstatus": 0,
    "doctype": "School",
    "institution": None,
    "location": "Fursungi",
    "modified": "2023-10-03 18:13:42.700013",
    "name": "Walnut School at Fursungi",
    "prefix": "FU",
    "school": "Walnut School at Fursungi"
   },
   {
    "custom_mgr_id": "47",
    "description": None,
    "docstatus": 0,
    "doctype": "School",
    "institution": None,
    "location": "Shivane",
    "modified": "2023-10-03 18:13:42.700013",
    "name": "Walnut School at Shivane",
    "prefix": "SH",
    "school": "Walnut School at Shivane"
   }
]


def execute():
    for template in data:
        if not frappe.db.exists("School",{'name': template.get('name')}):
            doc = frappe.get_doc(template)
            doc.insert()