frappe.listview_settings["CMAP"] = {
  add_fields: ["item_code_field"],
  onload: function (list_view) {
    if (
      frappe.user_roles.includes("Content Admin") ||
      frappe.user_roles.includes("Administrator") ||
      frappe.user_roles.includes("School Admin") ||
      frappe.user_roles.includes("System_Manager") ||
      frappe.user_roles.includes("Content Creator")
    )
      list_view.page.add_menu_item("Fetch Product Material", async () => {
        frappe.call({
          method:
            "edu_quality.edu_quality.doctype.cmap.cmap.calculate_all_product_materials",
          args: {
            name: "2024-2025---0111",
          },
          callback: function (r) {
            // frm.set_value('custom_sheet_number', r.message)
            frappe.msgprint({
              title: __("CMAP Material Calculation"),
              message: __("CMAP Material Calculation Scheduled Successfully. "),
              primary_action: {
                label: __("OK"),
                action: function () {
                  frappe.hide_msgprint();
                },
              },
            });
          },
        });
      });
  },
};
