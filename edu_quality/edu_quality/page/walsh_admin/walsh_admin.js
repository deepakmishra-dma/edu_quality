
frappe.pages['walsh-admin'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Walsh Admin',
        single_column: true
    });
    frappe.require(["/assets/nextai/node_modules/chatnext-ui/dist/index.css"]).then(() => {
        page.body[0].innerHTML = "<walsh-admin></walsh-admin>"
    })
}
