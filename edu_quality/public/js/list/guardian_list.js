frappe.listview_settings["Guardian"] = {
  refresh: function (listview) {
    listview.page.add_menu_item("Create Users", function () {
      frappe.call({
        method:
          "edu_quality.edu_quality.server_scripts.guardian.enqueue_gardian_user_creation",
        type: "POST",
        callback: function (response) {
          frappe.show_alert({
            message: __("Scheduled Guardian User Creation Successfully"),
            indicator: "green",
          });
        },
      });
    });
  },
};
