// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Fees Collection Report"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      width: "80",
    },
    {
      fieldname: "to_date",
      label: __("To Date"),
      fieldtype: "Date",
      width: "80",
    },
    {
      fieldname: "school",
      label: __("School"),
      fieldtype: "MultiSelectList",
      options: "School",
      width: "80",
      get_data: function (txt) {
        return frappe.db.get_link_options("School", txt);
      },
    },
    {
      fieldname: "payment_mode",
      label: __("Payment Mode"),
      fieldtype: "Link",
      options: "Mode of Payment",
      width: "80",
    },
  ],
};
