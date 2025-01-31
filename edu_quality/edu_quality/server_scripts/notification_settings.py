import frappe 

from frappe.desk.doctype.notification_settings.notification_settings import NotificationSettings 



def CustomNotificationSettings(NotificationSettings):
    
    def toggle_notifications(user: str, enable: bool = False):
        if not frappe.db.exists("Notification Settings",user):
            return 
        if frappe.db.get_value("Notification Settings",user,"enabled")!=enable:
            frappe.db.set_value("Notification Settings",user,"enabled",enable)

