import frappe
from frappe.website.utils import cache_html
from frappe.website.router import get_page_info_from_web_form
from frappe.website.page_renderers.document_page import DocumentPage


class WebFormPage(DocumentPage):
    def can_render(self):
        web_form = get_page_info_from_web_form(self.path)
        if web_form:
            self.doctype = "Web Form"
            self.docname = web_form.name
            self.doc = frappe.get_cached_doc(self.doctype, self.docname)
            return True
        else:
            return False

    def render(self):
        can_render = self.handle_deadlines()
        if not can_render:
            template = self.get_custom_html()
            return self.build_response(template)
        else:
            return super().render()

    @cache_html
    def get_custom_html(self):
        self.init_context()
        self.update_context()
        self.post_process_context()
        self.template_path = "templates/components/web_form.html"
        return frappe.get_template(self.template_path).render(self.context)

    def handle_deadlines(self):
        if self.doc.allow_deadlines:
            if self.doc.starts_on:
                if self.doc.starts_on > frappe.utils.now_datetime():
                    return False
            if self.doc.expires_on:
                if self.doc.expires_on < frappe.utils.now_datetime():
                    return False
        return True
