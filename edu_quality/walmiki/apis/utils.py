import frappe 


config = frappe.get_doc("Walmiki Configuration")

headers = {
  'Content-Type': 'application/json',
  'Authorization': config.get_password("auth")
}


def get_headers():
    return headers



def log_request(url,payload,response):
    log = frappe.new_doc("Walmiki Logs")
    log.timestamp = frappe.utils.now()
    log.url = url 
    log.payload = str(payload)
    log.response = str(response.json())
    log.status = "Success" if response.status_code == 200 else "Failed"
    log.save(ignore_permissions=True)

