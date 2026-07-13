// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.query_reports["CMAP Assignment"] = {
  filters: [
    {
      fieldname: "academic_year",
      fieldtype: "Link",
      options: "Academic Year",
      label: "Academic Year",
    },
    {
      fieldname: "school",
      label: __("School"),
      fieldtype: "Link",
      options: "School",
      reqd: 1,
    },
    {
      fieldname: "class",
      label: __("Class"),
      fieldtype: "Link",
      options: "Class Type",
      reqd: 1,
    },
    {
      fieldname: "subject",
      label: __("Subject"),
      fieldtype: "Link",
      reqd: 1,
      options: "Course",
    },
    {
      fieldname: "unit",
      label: __("Unit"),
      fieldtype: "Select",
      reqd: 1,
      options: "1\n2\n3\n4",
    },
  ],
};
