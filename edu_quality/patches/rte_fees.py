import frappe 

def execute():
    fees_list = frappe.db.get_all('Fees',[["Fees","split_payments","like","%null%"]])
    for fees in fees_list:
        frappe.db.set_value("Fee Component",{'parent':fees.name,'fees_category':"Curriculum Material Fee"},"label","CurriculamMaterialFee - HDFC")
        doc = frappe.get_doc("Fees",fees.name)
        doc.reload()
        doc.update_split()