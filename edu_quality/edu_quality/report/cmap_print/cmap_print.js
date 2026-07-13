// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
function changePrintCMAPReportData(value, id, rowIndex) {
  frappe.query_report.data[rowIndex][id] = value.value;
  calculateTotalQty(rowIndex);
}

function calculateTotalQty(rowIndex) {
  // const totalQty = frappe.query_report.data[rowIndex]["qty_for_shivane"] + frappe.query_report.data[rowIndex]["qty_for_wakad"] + frappe.query_report.data[rowIndex]["qty_for_fursungi"] + frappe.query_report.data[rowIndex]["extra_qty_per_school"]
  let totalQty = 0;
  Object.keys(frappe.query_report.data[rowIndex]).forEach((key) => {
    if (key.includes("qty_for_") && !key.includes("extra")) {
      totalQty +=
        Number(frappe.query_report.data[rowIndex][key]) +
        Number(frappe.query_report.data[rowIndex][`extra_${key}`]);
    }
  });

  frappe.query_report.data[rowIndex]["total_quantity"] = totalQty;
  const el = document.querySelector(
    `.dt-cell[data-row-index="${rowIndex}"] input#total_quantity`
  );
  if (el) el.value = totalQty;
}
frappe.query_reports["CMAP Print"] = {
  filters: [
    {
      fieldname: "academic_year",
      fieldtype: "Select",
      options: ["2023-2024", "2024-2025"],
      label: "Academic Year",
    },
    {
      fieldname: "class",
      label: __("Class"),
      fieldtype: "Link",
      options: "Class Type",
      reqd: 1,
      // get_data: function (txt) {
      // 	return frappe.db.get_link_options('Class Type', txt, {

      // 	});
      // }
    },
    {
      fieldname: "subject",
      label: __("Subject"),
      fieldtype: "MultiSelectList",
      reqd: 1,
      get_data: function (txt) {
        return frappe.db.get_link_options("Course", txt, {});
      },
    },
    {
      fieldname: "unit",
      label: __("Unit"),
      fieldtype: "MultiSelectList",
      reqd: 1,
      get_data: function (txt) {
        return [
          { value: 1, description: 1 },
          { value: 2, description: 2 },
          { value: 3, description: 3 },
          { value: 4, description: 4 },
        ];
      },
    },
    {
      fieldname: "start_plan_date",
      fieldtype: "Date",
      label: "Start Plan Date",
    },
    {
      fieldname: "end_plan_date",
      fieldtype: "Date",
      label: "End Plan Date",
    },
  ],
  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    if (column.id.includes("qty")) {
      value = `<input type="number" id="${column.id}" value=${value} oninput="changePrintCMAPReportData(this,'${column.id}','${row[0]?.rowIndex}')" />`;
    }
    if (column.id == "total_quantity") {
      value = `<input type="number" disabled="true" id="${column.id}" value=${value} oninput="changePrintCMAPReportData(this,'${column.id}','${row[0]?.rowIndex}')" />`;
    }
    return value;
  },
  onload: function (report) {
    addBulkEdit(report);

    report.page.add_inner_button(__("Create Order"), () => {
      let indexes = frappe.query_report.datatable.rowmanager.getCheckedRows();
      let selected_rows = indexes.map((i) => frappe.query_report.data[i]);

      if (selected_rows.length == 0) {
        frappe.msgprint(__("Select a row before creating Purchase Order"));
        return;
      }
      let message = `
				<div>

					<p>Are you sure you want to create a Purchase Order, for the selected rows ?</p>
				</div>`;

      const d = new frappe.ui.Dialog({
        title: "Select Supplier",
        fields: [
          {
            label: "Supplier",
            fieldname: "supplier",
            options: "Supplier",
            fieldtype: "Link",
          },
        ],
        primary_action: (values) => {
          const supplier = values.supplier || undefined;
          d.hide();
          frappe.confirm(__(message), () => {
            const academic_year = report.filters.find(
              (el) => el.fieldname === "academic_year"
            ).input.value;
            const class_name = report.filters.find(
              (el) => el.fieldname === "class"
            ).input.value;
            const unit = frappe.query_report.get_filter_value("unit");

            frappe.call({
              method:
                "edu_quality.edu_quality.report.cmap_print.cmap_print.create_purchase_order",
              args: {
                rows: selected_rows,
                academic_year: academic_year,
                class_name: class_name,
                unit: unit.join(","),
                supplier: supplier,
              },
              callback: function (r) {
                if (r.message) {
                  frappe.set_route(`/app/purchase-order/${r?.message?.name}`);
                }
              },
            });
          });
        },
      });
      d.show();
    });
  },
  get_datatable_options(options) {
    return Object.assign(options, {
      checkboxColumn: true,
    });
  },
};

function addBulkEdit(report) {
  report.page.add_inner_button(__("Bulk Edit Quantity"), async () => {
    const filters = getFilters();
    let indexes = frappe.query_report.datatable.rowmanager.getCheckedRows();
    let selected_rows = indexes.map((i) => frappe.query_report.data[i]);

    if (selected_rows.length == 0) {
      frappe.msgprint(__("Select a row before Bulk Editing"));
      return;
    }

    const extraFields = await frappe.call({
      method:
        "edu_quality.edu_quality.report.cmap_print.cmap_print.get_extra_fields",
      args: { filters: filters },
    });
    if (!extraFields.message) {
      return;
    }

    const options = extraFields.message.map((extraField) => ({
      label: extraField.label,
      value: extraField.fieldname,
    }));
    const d = new frappe.ui.Dialog({
      title: "Select a Field",
      fields: [
        {
          fieldname: "field_name",
          label: __("Field Name"),
          fieldtype: "Select",
          options: options,
          reqd: 1,
        },
        {
          fieldname: "field_value",
          label: __("Value"),
          fieldtype: "Int",
          reqd: 1,
        },
      ],
      primary_action: (values) => {
        const column = frappe.query_report.datatable.datamanager.columns.find(
          (col) => col.fieldname == values.field_name
        );

        indexes.forEach((index) => {
          const row = frappe.query_report.data[index];
          console.log(row);
          frappe.query_report.data[index] = {
            ...row,
            [values.field_name]: values.field_value,
          };
        });

        indexes.forEach((index, rowIndex) => {
          frappe.query_report.datatable.bodyRenderer.cellmanager.updateCell(
            column.colIndex,
            index,
            values.field_value,
            true
          );
        });
      },
    });
    d.show();
  });
}

function getFilters() {
  const filters = frappe.query_report.filters.reduce((acc, curr) => {
    return {
      ...acc,
      [curr.fieldname]: frappe.query_report.get_filter_value(curr.fieldname),
    };
  }, {});
  return filters;
}
