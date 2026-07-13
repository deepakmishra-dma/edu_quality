// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["Deposit Collection"] = {
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
      fieldname: "program",
      label: __("Class"),
      fieldtype: "MultiSelectList",
      options: "Class",
      width: "80",
      get_data: function (txt) {
        return frappe.db.get_link_options("Program", txt);
      },
    },
    {
      fieldname: "student_status",
      label: __("Student Status"),
      fieldtype: "Select",
      options: [
        "",
        "New student",
        "Current student",
        "Cancelled",
        "Not attending",
        "Defaulter",
        "Alumni",
      ],
      width: "80",
    },
    {
      fieldname: "academic_year",
      label: __("Academic Year"),
      fieldtype: "Link",
      options: "Academic Year",
      width: "80",
    },
  ],

  get_datatable_options(options) {
    return Object.assign(options, {
      checkboxColumn: true,
    });
  },
};
