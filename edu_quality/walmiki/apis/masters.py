import frappe 
import requests
import json
from edu_quality.walmiki.apis.utils import get_headers, log_request


@frappe.whitelist()
def upsert(doctype,docname,url):
    try:
        if frappe.db.exists(doctype,docname):
            doc = frappe.get_doc(doctype,docname)
            payload = doc.as_json()
            response = requests.request("POST", url, headers=get_headers(), data=payload)
            log_request(url,payload,response)
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
            payload = json.dumps({"data":data})
            response = requests.request("POST", url, headers=get_headers(), data=payload)
            return response.json()
    except Exception as e:
        frappe.logger("walmiki").exception(e)
        return e