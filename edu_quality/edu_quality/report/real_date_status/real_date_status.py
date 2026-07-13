# Copyright (c) 2024, Hybrowlabs Technologies and contributors
# For license information, please see license.txt

import frappe


def get_columns():
	columns = [
		{
			"fieldname": "teacher",
			"label": "Teacher",
			"fieldtype": "Link",
			"options": "Instructor",
			"width": 300,
		},
		{
			"fieldname": "real_date",
			"label": "Real Date",
			"fieldtype": "Date",
			"width": 200,
		},
		{
			"fieldname": "division",
			"label": "Division",
			"fieldtype": "Link",
			"options": "School",
			"width": 200,
		},
		{
			"fieldname": "subject",
			"label": "Subject",
			"fieldtype": "Link",
			"options": "Course",
			"width": 200,
		},
		{
			"fieldname": "period",
			"label": "Period",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "unit",
			"label": "Unit",
			"fieldtype": "Data",
			"width": 200,
		},
	]
	return columns


def get_data(filters):
	cmap_assign_table = frappe.qb.DocType("CMAP Assignment")
	cmap_table = frappe.qb.DocType("CMAP")

	academic_year = filters.get("academic_year")
	class_type = filters.get("class")
	subject = filters.get("subject")
	school = filters.get("school")
	show_blank = filters.get("show_blank")
	if not academic_year:
		return []

	condition_query = (
		(cmap_table.academic_year == academic_year)
		& (cmap_assign_table.school == school)
		& (cmap_table["class"] == class_type)
		& (cmap_table.subject == subject)
		& (cmap_table.reserved_for_portion_circular == 0)
	)

	if not show_blank:
		condition_query = condition_query & cmap_assign_table.real_date.isnotnull()

	cmap_query = (
		frappe.qb.from_(cmap_table)
		.inner_join(cmap_assign_table)
		.on(cmap_assign_table.parent == cmap_table.name)
		.where(condition_query)
		.select(
			cmap_assign_table.real_date,
			cmap_assign_table.teacher,
			cmap_assign_table.division,
			cmap_table.subject,
			cmap_table.period,
			cmap_table.unit,
		)
	)

	return cmap_query.run(as_dict=True)


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data
