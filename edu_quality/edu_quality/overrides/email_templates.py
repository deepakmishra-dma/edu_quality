import frappe
import urllib.parse
from frappe.email.doctype.email_template.email_template import EmailTemplate


class CustomEmailTemplate(EmailTemplate):
    def on_trash(self):
        self.validate_funnel()


    def on_update(self):
        self.validate_funnel()


    def validate_funnel(self):
        funnels = set(frappe.get_all(
            "Funnel Definition",
            {
                "element_type": "Action",
                "data": ["like", f'%"email_template": "{self.name}"%'],
                "parenttype": "Funnel"
            },
            pluck="parent",
        ))
        
        if len(funnels) > 0:
            msg = 'The Email Template "{}" is being used in the following Funnels:<ul style="padding-left: 15px;">{}</ul>'.format(self.name, "".join("<li>{}</li>".format(funnel) for funnel in funnels))
            # link = "/app/funnel?name="

            funnels_encoded = [urllib.parse.quote_plus(name) for name in funnels]
            funnels_string = ",".join(f'"{name}"' for name in funnels_encoded)
            link = f"/app/funnel?name=[\"in\",[{funnels_string}]]"
            msg += f"\n<div style='text-align: right;'><a href='{link}' target='_blank' class='btn btn-primary'>Open Funnel List</a></div>"
            
            frappe.throw(
                title=frappe._("Email Template in Use"),
                msg=frappe._(msg),
                as_list=True,
            )