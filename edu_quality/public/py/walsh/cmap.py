import frappe


@frappe.whitelist()
def get_students():
    user = frappe.session.user
    guardian = frappe.get_doc("Guardian", {"user": user})
    students = frappe.get_all("Student", filters={"guardian": guardian.name}, fields=["*"])
    return students


@frappe.whitelist()
def get_student_class_details(student):
    program_enrollments = frappe.get_all(
        "Program Enrollment",
        filters={"student": student},
        fields=["program", "student_group"],
    )
    if not len(program_enrollments):
        return {}

    program = program_enrollments[0]["program"]
    program_data = frappe.get_doc("Program", program)
    class_type = frappe.get_doc("Class Type", program_data.program_name)
    division = frappe.get_doc("Student Group", program_enrollments[0]["student_group"])

    return {
        "division": division,
        "program": program_data,
        "class": class_type
    }


@frappe.whitelist()
def get_all_cmaps(subject, unit, division):
    values = {
        'subject': subject,
        'unit': unit,
        "division": division
    }
    cmaps = frappe.db.sql('''
        select *,
         (select real_date from `tabCMAP Assignment` ta where division = %(division)s and real_date <= CURDATE() and
          ta.parent = c.name limit 1)          as real_date         from `tabCMAP` as c
        where subject = %(subject)s
        and unit = %(unit)s
        and name in (
            select parent from `tabCMAP Assignment` where real_date <= CURDATE()
        )
        order by real_date desc 
        ''', as_dict=1, values=values)
    cmap_names = [cmap.name for cmap in cmaps]
    all_products = frappe.get_all("Item Detail", filters={"parent": ["in", cmap_names]}, fields=["*"])
    item_names = [p.item for p in all_products]
    all_items = frappe.get_all("Item", fields=["*"], filters={"name": ["in", item_names]})
    broadcast_names = [product.broadcast for product in all_products if product.broadcast]
    homework_names = [product.home_work for product in all_products if product.home_work]
    cmap_material_names = broadcast_names + homework_names
    cmap_materials = frappe.get_all("Item CMAP Material", fields=["*"], filters={"name": ["in", cmap_material_names]})

    print(cmap_materials)

    for product in all_products:
        for item in all_items:
            if item.name == product.item:
                product['item_data'] = item
        for broadcast in cmap_materials:
            if broadcast.name == product.broadcast:
                product['broadcast_description'] = broadcast.description
        for homework in cmap_materials:
            if homework.name == product.home_work:
                product['homework_description'] = homework.description

    for cmap in cmaps:
        cmap.products = []
        for product in all_products:
            if product.parent == cmap.name:
                cmap.products.append(product)

    return cmaps
