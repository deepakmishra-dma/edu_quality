import frappe

data = [
    {
        "academic_year_name": "2016-2017",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2016-2017",
        "rolled_over": 0,
        "year_end_date": "2017-03-31",
        "year_start_date": "2016-04-01",
    },
    {
        "academic_year_name": "2017-2018",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2017-2018",
        "rolled_over": 0,
        "year_end_date": "2018-03-31",
        "year_start_date": "2017-04-01",
    },
    {
        "academic_year_name": "2019-2020",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2019-2020",
        "rolled_over": 0,
        "year_end_date": "2020-03-31",
        "year_start_date": "2019-04-01",
    },
    {
        "academic_year_name": "2020-2021",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2020-2021",
        "rolled_over": 0,
        "year_end_date": "2021-03-31",
        "year_start_date": "2020-04-01",
    },
    {
        "academic_year_name": "2021-2022",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2021-2022",
        "rolled_over": 0,
        "year_end_date": "2022-03-31",
        "year_start_date": "2021-04-01",
    },
    {
        "academic_year_name": "2022-2023",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2022-2023",
        "rolled_over": 0,
        "year_end_date": "2023-03-31",
        "year_start_date": "2022-04-01",
    },
    {
        "academic_year_name": "2023-2024",
        "custom_current_academic_year": 1,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2023-2024",
        "rolled_over": 0,
        "year_end_date": "2024-03-31",
        "year_start_date": "2023-04-01",
    },
    {
        "academic_year_name": "2024-2025",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 1,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2024-2025",
        "rolled_over": 0,
        "year_end_date": "2025-03-31",
        "year_start_date": "2024-04-01",
    },
    {
        "academic_year_name": "2025-2026",
        "custom_current_academic_year": 0,
        "custom_next_academic_year": 0,
        "docstatus": 0,
        "doctype": "Academic Year",
        "name": "2025-2026",
        "rolled_over": 0,
        "year_end_date": "2026-03-31",
        "year_start_date": "2025-04-01",
    },
]


def execute():
    for d in data:
        if not frappe.db.exists("Academic Year", {"name": d.get("name")}):
            doc = frappe.get_doc(d)
            doc.insert()
        else:
            doc = frappe.get_doc("Academic Year", d.get("name"))
            doc.update(d)
            doc.save()
