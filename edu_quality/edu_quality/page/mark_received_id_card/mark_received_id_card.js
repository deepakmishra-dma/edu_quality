frappe.pages["mark-received-id-card"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Mark Received ID Cards",
    single_column: true,
  });
  const el = page.wrapper.find(".container.page-body");
  // const el = document.querySelector('.container.page-body')
  const d = make_fieldgroup(el, [
    {
      label: "Enter Comma Separated Ref Nos",
      fieldname: "ref_nos",
      fieldtype: "Data",
    },
    {
      label: '<i class="fa fa-qrcode" aria-hidden="true"></i> Open Scanner',
      fieldname: "scanbtn",
      fieldtype: "Button",
      click: async () => {
        const images = await nativeInterface.execute("openWebViewScanner");
        d.set_value("ref_nos", images?.data);
        if (images?.data) {
          postScanQr(images?.data, true);
        }
      },
    },
    {
      label: "Submit",
      fieldname: "submitbtn",
      fieldtype: "Button",
      click: async () => {
        const qr_code = d["fields_dict"]["ref_nos"]["input"].value;
        if (qr_code) postScanQr(qr_code);
      },
    },
  ]);
};

function make_fieldgroup(parent, ddf_list) {
  fg = new frappe.ui.FieldGroup({
    fields: ddf_list,
    parent: parent,
  });
  fg.make();
  console.log(fg);
  return fg;
}

function postScanQr(key, qr_scan) {
  let d = new frappe.ui.Dialog({
    title: "Confirm?",

    primary_action_label: __("हो (Yes)"),
    primary_action: () => {
      frappe.call({
        method:
          "edu_quality.fees.doctype.permanent_id_card.permanent_id_card.mark_permanent_id_card_received",
        args: {
          id_cards: key,
          qr_scan: qr_scan,
          type: "POST",
        },
        callback: (r) => {
          console.log(r.message);

          frappe.msgprint({
            indicator: "green",
            title: __("Updated Successfully"),
            message: __(`Receipt ${key} marked as received`),
          });
          return d.set_value("ref_nos", "");
        },
      });
      d.hide();
    },
    secondary_action_label: __("नाही (No)"),
    secondary_action: () => {
      d.hide();
    },
  });
  d.show();
  d.set_message("Are you sure? नक्की ना?");
}
