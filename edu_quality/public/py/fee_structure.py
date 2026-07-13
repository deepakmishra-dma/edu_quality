import frappe


@frappe.whitelist()
def get_fee_structures(**kwargs):
	school = kwargs.get("school")
	institution = kwargs.get("institution")
	fees = []

	if school and not institution:
		fee_structures = frappe.get_all("Fee Structure", filters={"school": school})
		if fee_structures:
			for f in fee_structures:
				fee_structure = frappe.get_doc("Fee Structure", f.name)
				for component in fee_structure.components:
					data = {
						"class_name": fee_structure.program,
						"institution": institution,
						"academic_year": fee_structure.academic_year,
						"school": school,
						"fee_head_name": component.fees_category,
						"fee_head_type": component.fee_type,
						"amount": component.amount,
						"fee_structure": fee_structure.name,
					}
					fees.append(data)

	elif institution and not school:
		fee_structures = frappe.get_all("Fee Structure", filters={"institution": institution})
		if fee_structures:
			for f in fee_structures:
				fee_structure = frappe.get_doc("Fee Structure", f.name)
				for component in fee_structure.components:
					data = {
						"class_name": fee_structure.program,
						"institution": institution,
						"academic_year": fee_structure.academic_year,
						"school": school,
						"fee_head_name": component.fees_category,
						"fee_head_type": component.fee_type,
						"amount": component.amount,
						"fee_structure": fee_structure.name,
					}
					fees.append(data)

	elif institution and school:
		fee_structures = frappe.get_all(
			"Fee Structure", filters={"institution": institution, "school": school}
		)
		if fee_structures:
			for f in fee_structures:
				fee_structure = frappe.get_doc("Fee Structure", f.name)

				for component in fee_structure.components:
					data = {
						"class_name": fee_structure.program,
						"institution": institution,
						"academic_year": fee_structure.academic_year,
						"school": school,
						"fee_head_name": component.fees_category,
						"fee_head_type": component.fee_type,
						"amount": component.amount,
						"fee_structure": fee_structure.name,
					}
					fees.append(data)
	return fees
