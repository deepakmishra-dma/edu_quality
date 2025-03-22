import frappe 
import requests


headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Basic dmlrYXM6MTIzNA=='
}

@frappe.whitelist()
def upsert(doctype,docname,url):
    try:
        if frappe.db.exists(doctype,docname):
            doc = frappe.get_doc(doctype,docname)
            frappe.logger('walmiki').exception(doc.as_json())
            payload = doc.as_json()
            response = requests.request("POST", url, headers=headers, json=payload)
            return response.json()
        frappe.throw("Document Does Not Exist!")
    except Exception as e:
        frappe.logger("walmiki").exception(e)
        return e


@frappe.whitelist()
def bulk_upsert(doctype,url):
    try:
        docs = frappe.get_all(doctype)
        start=0
        for i in range(start,len(docs),100):
            data = []
            for doc in docs[i:i+100]:
                document = frappe.get_doc(doctype,doc.name)
                data.append(document.as_dict())
            payload = {"data":data}
            response = requests.request("POST", url, headers=headers, data=payload)
            return response.json()
    except Exception as e:
        frappe.logger("walmiki").exception(e)
        return e