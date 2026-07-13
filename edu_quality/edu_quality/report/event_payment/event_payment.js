// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Event Payment"] = {
  filters: [
    {
      fieldname: "event_detail",
      label: __("Event Detail"),
      fieldtype: "Link",
      options: "Event Detail",
      filters: {
        web_form: ["is", "set"],
      },
    },
    {
      fieldname: "payment_status",
      label: __("Payment Status"),
      fieldtype: "Select",
      options: ["", "Paid", "Unpaid"],
    },
  ],
};
