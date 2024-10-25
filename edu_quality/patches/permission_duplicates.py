import frappe 


def execute():
    try:
        process_data()
    except Exception as e:
        frappe.logger("permission").exception(e)


def process_data():
    roles = frappe.get_all("Role")
    for role in roles:
        print(role.name)
        docs = frappe.get_all("Custom DocPerm",filters={'role':role.name},fields=["parent"])
        for doc in docs:
            print(doc.parent)
            i=1
            permissions = frappe.get_all("Custom DocPerm",filters={'role':role.name,'parent':doc.parent},fields=["name","parent"])
            for permission in permissions:
                if i==1:
                    print("First Permission:" + permission.name)
                    i=0
                    doc = frappe.get_doc("Custom DocPerm",permission.name)
                    continue
                doc.reload()
                perm = frappe.get_doc("Custom DocPerm",permission.name)
                print("Duplicate:"+perm.name)
                if perm.select:
                    doc.select = 1 
                if perm.read:   
                    doc.read = 1
                if perm.write:
                    doc.write = 1
                if perm.submit:
                    doc.submit = 1
                if perm.cancel:
                    doc.cancel = 1
                if perm.amend:
                    doc.amend = 1
                if perm.delete:
                    doc.delete = 1
                if perm.report:
                    doc.report = 1
                if perm.export:
                    doc.export = 1
                if perm.print:
                    doc.print = 1
                if perm.email:
                    doc.email = 1
                if perm.share:
                    doc.share = 1
                doc.save(ignore_permissions=True)
                frappe.delete_doc("Custom DocPerm",perm.name,ignore_permissions=True)

