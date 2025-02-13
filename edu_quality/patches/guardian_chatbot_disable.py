import frappe

def execute():
    pending_guardians = frappe.db.get_all(
        "Contact",
        filters=[["name", "like", "%walsh:%"], ["chatbot_disabled", "=", "0"]],
        fields=["name", "chatbot_disabled"],
    )
    for guardian in pending_guardians:
        name = guardian.get("name")
        chatbot_disabled = guardian.get("chatbot_disabled")

        if chatbot_disabled == 0:
            frappe.db.set_value("Contact", name, "chatbot_disabled", 1)
