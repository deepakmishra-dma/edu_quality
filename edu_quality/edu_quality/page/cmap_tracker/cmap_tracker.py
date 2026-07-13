import json

import frappe
import frappe.utils
from frappe.query_builder import Order
from frappe.query_builder.functions import Cast

from edu_quality.edu_quality.server_scripts.utils import current_academic_year
from edu_quality.public.py.utils import check_admin_roles, check_roles


# edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.get_cmap
@frappe.whitelist()
def get_cmap(**filters):
	cmap_table = frappe.qb.DocType("CMAP")
	cmap_assign_table = frappe.qb.DocType("CMAP Assignment")
	products_table = frappe.qb.DocType("Item Detail")
	item_table = frappe.qb.DocType("Item")
	teacher = calculate_teacher_value(filters.get("teacher"))
	user_roles = frappe.get_roles(frappe.session.user)
	if check_admin_roles(user_roles, ["Principal", "Vice Principal", "HoD"]) and not teacher:
		teacher = "ALL"

	filtered_cmap_query = (
		frappe.qb.from_(cmap_table)
		.where(
			(cmap_table.academic_year == filters.get("academic_year"))
			& (cmap_table.subject == filters.get("subject"))
			& (cmap_table.unit == filters.get("unit"))
			& (cmap_table["class"] == filters.get("class"))
			& (cmap_table.reserved_for_portion_circular == 0)
		)
		.select(
			cmap_table.name,
			cmap_table.academic_year,
			cmap_table.period,
			cmap_table.plan_date,
			# cmap_table.broadcast_text.as_("broadcast"),
			# cmap_table.parent_notes.as_("parent_note"),
			# cmap_table.home_work,
			# cmap_table.class_work,
			# cmap_table.material_required,
		)
	)

	filtered_cmap_product_query = (
		frappe.qb.from_(filtered_cmap_query)
		.inner_join(products_table)
		.on(filtered_cmap_query.name == products_table.parent)
		.inner_join(item_table)
		.on(products_table.item == item_table.name)
		.select(
			filtered_cmap_query.name,
			products_table.broadcast,
			products_table.item.as_("item_code"),
			products_table.parent_note,
			products_table.class_work,
			products_table.material_required,
			products_table.home_work,
			products_table.textbook,
			products_table.chapter,
			item_table.custom_product_url,
		)
	)

	products_data = filtered_cmap_product_query.run(as_dict=True)
	filtered_assigned_query = (
		frappe.qb.from_(filtered_cmap_query)
		.inner_join(cmap_assign_table)
		.on(filtered_cmap_query.name == cmap_assign_table.parent)
	)
	div_condition = (cmap_assign_table.division == filters.get("division")) & (
		cmap_assign_table.school == filters.get("school")
	)

	if not filters.get("division"):
		div_condition = (cmap_assign_table.division.isnotnull()) & (
			cmap_assign_table.school == filters.get("school")
		)

	if teacher != "ALL":
		filtered_assigned_query = filtered_assigned_query.where(
			(cmap_assign_table.teacher == teacher) & div_condition
		)
	else:
		filtered_assigned_query = filtered_assigned_query.where(div_condition)

	filtered_assigned_query = filtered_assigned_query.orderby(
		Cast(filtered_cmap_query.period, "UNSIGNED"), Order.asc
	).select(
		filtered_cmap_query.star,
		cmap_assign_table.teacher,
		cmap_assign_table.school,
		cmap_assign_table.division,
		cmap_assign_table.real_date,
	)
	return cocatenate_cmap(filtered_assigned_query.run(as_dict=True), products_data)


def cocatenate_cmap(data, products_data):
	product_hash = {}
	for product in products_data:
		cmap_name = product.get("name")

		if cmap_name not in product_hash:
			product_hash[cmap_name] = [product]
		else:
			product_hash[cmap_name].append(product)

	for cmap in data:
		cmap_name = cmap.get("name")
		if cmap_name in product_hash:
			cmap["products"] = [
				{
					"item_code": i.get("item_code"),
					"custom_product_url": i.get("custom_product_url"),
				}
				for i in product_hash[cmap_name]
			]

			for type_material in [
				"broadcast",
				"home_work",
				"parent_note",
				"material_required",
				"class_work",
			]:
				cmap[type_material] = find_first_non_empty_key(product_hash[cmap_name], type_material)

			cmap["chapter_name"] = ",".join(set([i.get("chapter") for i in product_hash[cmap_name]]))
	return data


# edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.update
@frappe.whitelist()
def update(filters, cmap_data):
	filters = json.loads(filters) if isinstance(filters, str) else filters
	cmap_data = json.loads(cmap_data) if isinstance(cmap_data, str) else cmap_data
	teacher = calculate_teacher_value(filters.get("teacher"))
	user_roles = frappe.get_roles(frappe.session.user)
	is_admin = check_admin_roles(user_roles, ["Principal", "Vice Principal", "HoD", "Clerk"])

	for cmap_name in cmap_data:
		cmap = frappe.get_doc("CMAP", cmap_name)
		modified = False

		updated_data = cmap_data.get(cmap_name)
		division = updated_data.get("division") or filters.get("division")
		real_date = updated_data.get("real_date")
		real_date_updated_on = frappe.utils.get_datetime()
		local_teacher = updated_data.get("teacher")

		if not teacher and is_admin:
			teacher = local_teacher

		for item in cmap.table_vwbr:
			allow_edit = is_admin or (not item.real_date)

			if item.school == filters.get("school") and item.division == division and item.teacher == teacher:
				# Update existing teacher

				if allow_edit or real_date:
					frappe.db.set_value("CMAP Assignment", item.name, "real_date", real_date)
					# Updating the Real Date for CMAP Consolidated Notification..
					frappe.db.set_value(
						"CMAP Assignment",
						item.name,
						"real_date_updated_on",
						real_date_updated_on,
					)
		#             item.real_date = real_date
		#             modified = True

		# if modified:
		#     cmap.save(ignore_permissions=True)

	return


# edu_quality.edu_quality.page.cmap_tracker.cmap_tracker.calculate_teacher_value
@frappe.whitelist()
def calculate_teacher_value(value_for_admin):
	user_roles = frappe.get_roles(frappe.session.user)
	teacher = ""
	if check_admin_roles(user_roles, ["Principal", "Vice Principal", "HoD"]):
		return value_for_admin

	if check_roles(user_roles, ["Teacher", "Instructor"]):
		teacher = frappe.session.user

	instructor_table = frappe.qb.DocType("Instructor")
	user_table = frappe.qb.DocType("User")
	employee_table = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(employee_table)
		.inner_join(user_table)
		.on(employee_table.user_id == user_table.name)
		.where(user_table.name == teacher)
		.inner_join(instructor_table)
		.on(instructor_table.employee == employee_table.name)
		.select(instructor_table.name)
	)
	if not teacher:
		return frappe.msgprint("You don't have permission to see the cmap of the given teacher", "Error")
	data = query.run(as_dict=True)
	if len(data):
		return data[0].get("name")

	frappe.msgprint("Teacher couldn't be found, Please Contact Admin", "Error")
	return frappe.redirect("/app")


@frappe.whitelist()
def get_teacher_details(value_for_admin):
	teacher = calculate_teacher_value(value_for_admin)
	if teacher:
		school = frappe.db.get_value("Instructor", filters={"name": teacher}, fieldname="custom_school")
		return teacher, current_academic_year(), school
	return teacher, None, None


def find_first_non_empty_key(objects_list, key):
	for obj in objects_list:
		if obj.get(key):
			return obj.get(key)
	return None
