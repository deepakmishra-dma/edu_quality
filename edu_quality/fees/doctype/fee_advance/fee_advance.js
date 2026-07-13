// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fee Advance", {
  refresh: function (frm) {
    if (frm.doc.docstatus > 0) {
      frm.add_custom_button(
        __("Accounting Ledger"),
        function () {
          frappe.route_options = {
            voucher_no: frm.doc.name,
            from_date: frm.doc.posting_date,
            to_date: moment(frm.doc.modified).format("YYYY-MM-DD"),
            company: frm.doc.company,
            group_by: "",
            show_cancelled_entries: frm.doc.docstatus === 2,
          };
          frappe.set_route("query-report", "General Ledger");
        },
        __("View")
      );
      frm.add_custom_button(
        __("Payment Entry"),
        function () {
          frappe.set_route("List", "Payment Entry", {
            reference_name: frm.doc.name,
          });
        },
        __("View")
      );
      frm.add_custom_button(
        __("Payment Request"),
        function () {
          frappe.set_route("List", "Payment Request", {
            "Payment Request Reference.reference_name": frm.doc.name,
          });
        },
        __("View")
      );
      frm.add_custom_button(__("Modify Payment Plan"), function () {
        const doc = frm.doc;
        const dialog = new frappe.ui.Dialog({
          title: "Modify Payment Plan",
          fields: [
            {
              label: "Payment Plan",
              fieldname: "payment_plan",
              fieldtype: "Link",
              options: "Payment Plan",
              get_query: function () {
                return {
                  doctype: "Payment Plan",
                  filters: {
                    fee_structure: doc.fee_structure,
                    name: ["!=", doc.payment_plan],
                  },
                };
              },
            },
          ],
          size: "large",
          primary_action_label: "Submit",
          primary_action: async function (values) {
            doc.payment_plan = values.payment_plan;
            await frappe.call({
              method:
                "edu_quality.edu_quality.server_scripts.payment_plan.change_payment_plan",
              type: "POST",
              args: {
                payment_plan: values.payment_plan,
                doctype: doc.doctype,
                fee_name: doc.name,
              },
              callback: function (response) {
                frappe.show_alert({
                  message: __(response.message),
                  indicator: "green",
                });
              },
              async: false,
            });
            dialog.hide();
            frm.reload_doc();
          },
        });
        dialog.show();
      });
      frm.add_custom_button(
        __("Add Discount"),
        function () {
          let d = new frappe.ui.Dialog({
            title: "Add Discount",
            fields: [
              {
                label: "Discount Name",
                fieldname: "discount_name",
                fieldtype: "Link",
                options: "Discount Configuration",
                get_query: function () {
                  return {
                    doctype: "Discount Configuration",
                    filters: {
                      fee_structure: frm.doc.fee_structure,
                      type: "One Time",
                    },
                  };
                },
              },
            ],
            size: "large",
            primary_action_label: "Submit",
            primary_action(values) {
              frappe.call({
                method: "edu_quality.public.py.discount.add_discount",
                type: "POST",
                args: {
                  discount: values.discount_name,
                  doctype: frm.doc.doctype,
                  fee_name: frm.doc.name,
                },
                callback: function (response) {
                  frappe.show_alert({
                    message: __(response.message),
                    indicator: "green",
                  });
                  frm.reload_doc();
                },
              });
              d.hide();
            },
          });

          d.show();
        },
        __("Discount")
      );
      frm.add_custom_button(
        __("Remove Discount"),
        function () {
          let d = new frappe.ui.Dialog({
            title: "Remove Discount",
            fields: [
              {
                label: "Discount Name",
                fieldname: "discount_name",
                fieldtype: "Link",
                options: "Discount Configuration",
                get_query: function () {
                  return {
                    doctype: "Discount Configuration",
                    filters: {
                      fee_structure: frm.doc.fee_structure,
                      type: "One Time",
                    },
                  };
                },
              },
            ],
            size: "large",
            primary_action_label: "Submit",
            primary_action(values) {
              frappe.call({
                method: "edu_quality.public.py.discount.remove_discount",
                type: "POST",
                args: {
                  discount: values.discount_name,
                  doctype: frm.doc.doctype,
                  fee_name: frm.doc.name,
                },
                callback: function (response) {
                  frappe.show_alert({
                    message: __(response.message),
                    indicator: "orange",
                  });
                  frm.reload_doc();
                },
              });
              d.hide();
            },
          });

          d.show();
        },
        __("Discount")
      );
      manualCollection(frm); // Manual Collection Button
    }
  },
});

function manualCollection(frm) {
  const table_fields = [
    {
      fieldname: "company",
      fieldtype: "Link",
      in_list_view: 1,
      label: "Company",
      options: "Company",
      reqd: 1,
    },
    {
      fieldname: "amount",
      fieldtype: "Currency",
      in_list_view: 1,
      label: "Amount",
      reqd: 1,
    },
    {
      fieldname: "reference_number",
      fieldtype: "Data",
      in_list_view: 1,
      label: "Reference Number",
      reqd: 1,
    },
  ];

  let html_content = ``;
  let pdf_url = "";

  async function getPaymentRequest(reference_name, docstatus) {
    let found = false;
    const result = await frappe.db.get_value(
      "Payment Request",
      { reference_name: reference_name, docstatus: docstatus },
      "name"
    );

    if (result && result.message && result.message.name) {
      found = true;
    }

    return found;
  }

  frm.add_custom_button("Manual Collection", async function () {
    let paymentRequestExists = await getPaymentRequest(frm.doc.name, 1);
    if (!paymentRequestExists) {
      frappe.msgprint(`Payment Request for ${frm.doc.name} does not Exists`);
      return;
    }

    if (frm.doc.outstanding_amount == 0) {
      frappe.msgprint(`Fee Advance ${frm.doc.name} is Already Paid`);
      return;
    }
    let d = new frappe.ui.Dialog({
      title: "Manual Collection",
      fields: [
        {
          label: "Payment Term",
          fieldname: "payment_term",
          fieldtype: "Select",
          options: frm.doc.payment_term,
          onchange: function (e) {
            frappe.call({
              method:
                "edu_quality.edu_quality.server_scripts.manual_payment.get_payment_details",
              type: "POST",
              args: {
                fee: frm.doc.name,
                doctype: frm.doc.doctype,
                term: frm.doc.payment_term,
              },
              callback: function (response) {
                console.log(response.message);
                d.set_df_property("table", "data", response.message);
              },
            });
            showUnderTaking(d);
          },
        },
        {
          label: "Payment Mode",
          fieldname: "payment_mode",
          fieldtype: "Link",
          options: "Mode of Payment",
        },
        {
          fieldtype: "Table",
          fieldname: "table",
          label: "Cheque/ DD Details",
          cannot_add_rows: true,
          in_place_edit: true,
          reqd: 1,
          data: [],
          fields: table_fields,
        },
        {
          fieldtype: "Check",
          fieldname: "undertaking_check",
          label: `Accept Undertaking Before Making Payment <a href="${pdf_url}" target='_black'>Click here</a>`,
          hidden: 1,
          onchange: function (e) {
            let payment_term = d.get_value("payment_term");
            if (this.value) {
              d.set_df_property(
                "undertaking_content",
                "options",
                `<script>function verifyOtp(){
									const btn_value = document.getElementById('doc_value');
									const otp = document.getElementById('otp');
									const otp_area = document.getElementById('otp-area');

									frappe.call({
										method:"edu_quality.public.py.undertaking.verify_undertaking_otp",
										args: {
											"otp": otp.value,
											"fee_advance":btn_value.value
										},
										callback: function(r) {
											if(r.message === true){
												showAlert('OTP Verified Successfully', 'green');
												const x = document.querySelector(".btn-modal-primary")
												x.style.display = 'inline-block';
												otp_area.classList.add('hidden');
												$("input[data-fieldname='undertaking_check']").prop('readonly', true);
												submitUndertaking();
											}else{
												showAlert('Incorrect OTP Entered, please try again.', 'red');
												otp.style.border = "border-danger";

											}
										}
									});
								}function showAlert(message, indicator){
									frappe.show_alert({
										message: __(message),
										indicator: indicator
									});
								}
								function submitUndertaking() {
								const otp = document.getElementById('otp').value;
								fetch('https://ipinfo.io/json')
									.then(response => response.json())
									.then(data => {
										let userIpAddress = data.ip;
										let userAgentInfo = navigator.userAgent;
										frappe.call({
											method: 'edu_quality.public.py.utils.handle_undertaking_submission',
											args: {
												ip_address: userIpAddress,
												browser_info: userAgentInfo,
												fee_advance: document.getElementById('doc_value').value,
												otp: otp,
												payment_term: '${payment_term}'
											},
											callback: function (response) {
												if (response.message === 'success') {
													// Data sent successfully.
												} else {
													// Handle the error here.
												}
											},
											error: function (xhr, textStatus, errorThrown) {
												console.error('Error sending data:', errorThrown);
											},
										});
									});
							}</script><div class="form-inline m-1" id="otp-area">
								<input type="number" class="form-control p-1" id="otp" placeholder="Enter OTP">
								<textarea id="doc_value" rows="15" class="hidden">${frm.doc.name}</textarea>
								<button id="btn_value" class="form-control btn-dark m-3 p-1" onclick="verifyOtp()">Submit OTP</button>
							</div>`
              );
            } else {
              d.set_df_property("undertaking_content", "options", ``);
            }
          },
        },
        {
          fieldtype: "HTML",
          fieldname: "undertaking_content",
          label: "",
          options: html_content,
        },
      ],
      size: "large",
      primary_action_label: "Submit",
      primary_action: onDialogSubmit,
    });

    d.show();

    function showUnderTaking(d) {
      frappe.call({
        method:
          "edu_quality.edu_quality.server_scripts.manual_payment.get_unpaid_terms",
        type: "POST",
        args: {
          fee: frm.doc.name,
          doctype: "Fee Advance",
          payment_term: d.get_value("payment_term"),
        },
        callback: function (response) {
          pdf_url = response.message.undertaking_url;
          if (response.message.undertaking_enabled) {
            if (!response.message.undertaking_accepted) {
              d.set_df_property("undertaking_check", "hidden", 0);
              d.set_df_property("undertaking_check", "reqd", 1);
              // hide the submit button if undertaking is not accepted
              setTimeout(() => {
                console.log("Delayed for 1 second.");
                console.log(document.querySelector(".btn-modal-primary"));
                const x = document.querySelector(".btn-modal-primary");
                x.style.display = "none";
              }, 1000);
              // Send OTP
              d.fields_dict.undertaking_check.input.onclick = function () {
                if (d.fields_dict.undertaking_check.input.checked) {
                  sendOtp(frm);
                }
              };
            } else {
              d.set_df_property("undertaking_check", "hidden", 0);
              d.set_df_property("undertaking_check", "default", 1);
              d.set_df_property("undertaking_check", "read_only", 1);
            }
          }
        },
      });
    }

    function onDialogSubmit(values) {
      console.log(values);
      if (!values.undertaking_check) {
        frappe.throw("Please select Terms and conditions");
      } else {
        frappe.call({
          method:
            "edu_quality.edu_quality.server_scripts.manual_payment.manual_payment",
          type: "POST",
          args: {
            term: values.payment_term,
            fee: frm.doc.name,
            data: values.table,
            payment_mode: values.payment_mode,
          },
          callback: function (response) {
            showAlert(response.message, "green");
            frm.reload_doc();
          },
        });
      }
      d.hide();
    }
  });

  function sendOtp(frm) {
    frappe.call({
      method: "edu_quality.public.py.undertaking.generate_undertaking_otp",
      args: {
        fee_advance: frm.doc.name,
      },
      callback: function (r) {
        if (r.message === true) {
          showAlert("OTP has been sent successfully.", "green");
        } else {
          showAlert("Error while sending OTP.", "red");
        }
      },
    });
  }

  function showAlert(message, indicator) {
    frappe.show_alert({
      message: __(message),
      indicator: indicator,
    });
  }
}
