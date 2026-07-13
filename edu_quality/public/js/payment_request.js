// make child table read only if current user role is student
frappe.ui.form.on("Payment Request", {
  refresh: function (frm) {
    addPaymentPlanDetails(frm);
  },
});

function addPaymentPlanDetails(frm) {
  if (!frm.is_new()) {
    frappe.call({
      method: "edu_quality.public.py.payment_request.get_payment_plan_details",
      args: {
        payment_request: frm.selected_doc.name,
      },
      callback: function (r) {
        if (r.message) {
          frm.$wrapper[0].querySelector("#payment_plan").innerHTML = r.message
            ? `
                        <table class="table table-bordered">
                            <tr>
                                <td>Payment Plan</td>
                                <td>${r.message}</td>
                            </tr>
                        </table>
                    `
            : `<center><p>Payment Plan Not Found</p></center>`;
        }
      },
    });
  }
}
