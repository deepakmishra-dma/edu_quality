frappe.ui.form.on("Payment Entry", {
  refresh: function (frm) {
    frm.set_query("paid_to", function () {
      frm.events.validate_company(frm);

      var account_types = ["Receive", "Internal Transfer"].includes(
        frm.doc.payment_type
      )
        ? ["Bank", "Cash"]
        : [frappe.boot.party_account_types[frm.doc.party_type]];
      if (frm.doc.payment_type == "Pay") {
        account_types = ["Payable"];
      }
      return {
        filters: {
          account_type: ["in", account_types],
          is_group: 0,
          company: frm.doc.company,
        },
      };
    });
  },
});
