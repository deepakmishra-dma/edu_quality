import frappe 


def execute():
    try:
        fee_list = frappe.db.get_all("Fees",filters=[["Payment Schedule","payment_amount","=",0],["Fees","payment_plan","not like","%P1%"]])
        for fee in fee_list:
            doc = frappe.get_doc("Fees",fee.name)
            term1 = 0
            term2 = 0
            for term in doc.payment_schedule:
                if term.payment_term == "Term 1" and term.payment_amount>0:
                    continue 
                if term.payment_term == "Term 2":
                    term2 = term.payment_amount 
                if term.payment_term == 'Term 3':
                    term1 = term2-term.payment_amount
                    term2 = term.payment_amount
                    break 
            
            frappe.db.set_value("Payment Schedule",{'parent':fee.name,"payment_term":"Term 1"},"payment_amount",term1)
            frappe.db.set_value("Payment Schedule",{'parent':fee.name,"payment_term":"Term 2"},"payment_amount",term2)
            frappe.db.set_value("Payment Schedule",{'parent':fee.name,"payment_term":"Term 1"},"outstanding",term1)
            frappe.db.set_value("Payment Schedule",{'parent':fee.name,"payment_term":"Term 2"},"outstanding",term2)

            if frappe.db.exists("Payment Request",{'reference_name':fee.name,"payment_term":"Term 1","docstatus":1}):
                pr = frappe.get_doc("Payment Request",{'reference_name':fee.name,"payment_term":"Term 1","docstatus":1})
                pr.cancel()

            if frappe.db.exists("Payment Request",{'reference_name':fee.name,"payment_term":"Term 2","docstatus":1}):
                pr = frappe.get_doc("Payment Request",{'reference_name':fee.name,"payment_term":"Term 2","docstatus":1})
                pr.cancel()
            doc.reload()
            frappe.enqueue(
                        "edu_quality.public.py.student.create_payment_request",
                        fee=doc,
                        term="Term 1",
                        is_async=True,
                        queue="long",
                        timeout=1800,
                    )
            frappe.enqueue(
                        "edu_quality.public.py.student.create_payment_request",
                        fee=doc,
                        term="Term 2",
                        is_async=True,
                        queue="long",
                        timeout=1800,
                    )
    except Exception as e:
        frappe.logger('term2').exception(e)