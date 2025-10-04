
frappe.ui.form.on('Fees', {
    refresh: function (frm) {
        generate_payment_link(frm);
        partial_payment(frm);
        frm.add_custom_button(__('Split Deposits'), function () {
            frappe.call({
                method: "edu_quality.edu_quality.server_scripts.fees.separate_deposits",
                type: "POST",
                args: {
                    fees: frm.doc.name
                },
                callback: function (response) {
                    if (response.message) {
                        frappe.show_alert("Deposits Separated!",)
                        frm.reload_doc();
                    }
                    else {
                        frappe.show_alert("Something went Wrong!")
                    }
                }
            });

        }, __("Action"));

        frm.add_custom_button(__('Add Discount'), function () {
            let d = new frappe.ui.Dialog({
                title: 'Add Discount',
                fields: [
                    {
                        label: 'Discount Name',
                        fieldname: 'discount_name',
                        fieldtype: 'Link',
                        options: "Discount Configuration",
                        reqd: 1,
                        get_query: function () {
                            return {
                                doctype: 'Discount Configuration',
                                filters: {
                                    fee_structure: frm.doc.fee_structure,
                                    type: "One Time"
                                },
                            };
                        }
                    },
                    {
                        label: 'Term',
                        fieldname: 'term',
                        fieldtype: 'Link',
                        reqd: 1,
                        options: "Payment Term",
                    }
                ],
                size: 'large',
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        method: "edu_quality.public.py.discount.add_discount",
                        type: "POST",
                        args: {
                            discount: values.discount_name,
                            fee_name: frm.doc.name,
                            term: values.term
                        },
                        callback: function (response) {
                            frappe.show_alert({
                                message: __(response.message),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    });
                    d.hide();
                }
            });

            d.show();

        }, __("Discount"));


        frm.add_custom_button(__('Remove Discount'), function () {
            let d = new frappe.ui.Dialog({
                title: 'Remove Discount',
                fields: [
                    {
                        label: 'Discount Name',
                        fieldname: 'discount_name',
                        fieldtype: 'Link',
                        options: "Discount Configuration",
                        get_query: function () {
                            return {
                                doctype: 'Discount Configuration',
                                filters: {
                                    fee_structure: frm.doc.fee_structure,
                                    type: "One Time"
                                },
                            };
                        }
                    }
                ],
                size: 'large',
                primary_action_label: 'Submit',
                primary_action(values) {
                    frappe.call({
                        method: "edu_quality.public.py.discount.remove_discount",
                        type: "POST",
                        args: {
                            discount: values.discount_name,
                            fee_name: frm.doc.name
                        },
                        callback: function (response) {
                            frappe.show_alert({
                                message: __(response.message),
                                indicator: 'orange'
                            });
                            frm.reload_doc();
                        }
                    });
                    d.hide();
                }
            });

            d.show();
        }, __("Discount"));

        frappe.call({
            method: "edu_quality.edu_quality.server_scripts.fees.pr_count",
            type: "POST",
            args: {
                pr: frm.doc.name
            },
            callback: function (response) {
                if (response.message > 0) {
                    frm.add_custom_button(__('Modify Payment Plan'), function () {
                        const doc = frm.doc;
                        const dialog = new frappe.ui.Dialog({
                            title: 'Modify Payment Plan',
                            fields: [
                                {
                                    label: 'Payment Plan',
                                    fieldname: 'payment_plan',
                                    fieldtype: 'Link',
                                    options: "Payment Plan",
                                    get_query: function () {
                                        return {
                                            doctype: 'Payment Plan',
                                            filters: {
                                                fee_structure: doc.fee_structure,
                                                name: ["!=", doc.payment_plan]
                                            },
                                        };
                                    }
                                }
                            ],
                            size: 'large',
                            primary_action_label: 'Submit',
                            primary_action: async function (values) {
                                doc.payment_plan = values.payment_plan;
                                await frappe.call({
                                    method: "edu_quality.edu_quality.server_scripts.payment_plan.change_payment_plan",
                                    type: "POST",
                                    args: {
                                        payment_plan: values.payment_plan,
                                        doctype: doc.doctype,
                                        fee_name: doc.name
                                    },
                                    callback: function (response) {
                                        frappe.show_alert({
                                            message: __(response.message),
                                            indicator: 'green'
                                        });
                                    },
                                    async: false
                                });
                                dialog.hide();
                                frm.reload_doc();
                            }
                        });
                        dialog.show();
                    }, __("Action"));
                }
            }
        });

        if (frm.doc.need_otp === 1 && frm.doc.parent_otp === 0) {
            frm.add_custom_button(__('Send OTP'), function () {
                frappe.call({
                    method: "edu_quality.public.py.utils.generate_otp",
                    args: {
                        "fee": frm.doc.name
                    },
                    callback: function (r) {
                        if (r.message === true) {
                            frappe.show_alert({
                                message: __("OTP Sent Successfully"),
                                indicator: 'green'
                            });
                        } else {
                            frappe.show_alert({
                                message: __("OTP not sent, Please try again"),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }, __("OTP"));
            frm.add_custom_button(__('Verify OTP'), function () {
                let d = new frappe.ui.Dialog({
                    title: 'Verify OTP',
                    fields: [
                        {
                            label: 'OTP',
                            fieldname: 'otp',
                            fieldtype: 'Int'
                        }
                    ],
                    primary_action_label: 'Submit',
                    primary_action(values) {
                        frappe.call({
                            method: "edu_quality.public.py.utils.verify_otp",
                            args: {
                                "fee": frm.doc.name,
                                "otp": values.otp
                            },
                            callback: function (r) {
                                if (r.message === true) {
                                    frappe.show_alert({
                                        message: __("OTP Verified Successfully"),
                                        indicator: 'green'
                                    });
                                    frm.doc.parent_otp = 1;
                                    frm.save('Update');
                                } else {
                                    frappe.show_alert({
                                        message: __("Invalid OTP, Please try again"),
                                        indicator: 'red'
                                    });
                                }
                            }
                        });
                        d.hide();
                        frm.refresh();
                    }
                });
                d.show();
            }, __("OTP"));
        }
        manualCollection(frm); // Manual Collection Button
    }
});


function manualCollection(frm) {
    frm.remove_custom_button("Payment Request", "Create");
    frm.remove_custom_button("Payment", "Create");
    const table_fields = [
        { fieldname: "company", fieldtype: "Link", in_list_view: 1, label: "Company", options: "Company", reqd: 1 },
        { fieldname: "amount", fieldtype: "Currency", in_list_view: 1, label: "Amount", reqd: 1 },
        { fieldname: "reference_number", fieldtype: "Data", in_list_view: 1, label: "Reference Number", reqd: 1 }
    ];

    let pdf_url = '';
    let html_content = '';
    let unpaid_terms = [];
    getTermAndUnderTaking();

    frm.add_custom_button("Manual Collection", async function () {
        let paymentRequestExists = await getPaymentRequest(frm.doc.name, 1);
        if (!paymentRequestExists) {
            frappe.msgprint(`Payment Request for ${frm.doc.name} does not Exists`);
            return;
        }

        if (frm.doc.outstanding_amount == 0) {
            frappe.msgprint(`Fees ${frm.doc.name} is Already Paid`);
            return;
        }

        let d = new frappe.ui.Dialog({
            title: 'Manual Collection',
            fields: [
                {
                    label: 'Payment Term',
                    fieldname: 'payment_term',
                    fieldtype: 'Select',
                    options: unpaid_terms,
                    onchange: function (e) {
                        frappe.call({
                            method: "edu_quality.edu_quality.server_scripts.manual_payment.get_payment_details",
                            type: "POST",
                            args: { fee: frm.doc.name, doctype: frm.doc.doctype, term: d.get_value('payment_term') },
                            callback: function (response) {
                                d.set_df_property('table', 'data', response.message);
                            }
                        });
                        showUnderTaking(d);
                    }
                },
                {
                    label: 'Payment Mode',
                    fieldname: 'payment_mode',
                    fieldtype: 'Link',
                    options: "Mode of Payment"
                },
                {
                    fieldtype: "Table",
                    fieldname: "table",
                    label: "Cheque/ DD Details",
                    cannot_add_rows: true,
                    in_place_edit: true,
                    reqd: 1,
                    data: [],
                    fields: table_fields
                },
                {
                    fieldtype: "Check",
                    fieldname: "undertaking_check",
                    label: `Accept Undertaking Before Making Payment <a href="${pdf_url}" target='_black'>Click here</a>`,
                    hidden: 1,
                    onchange: function (e) {
                        let payment_term = d.get_value('payment_term');
                        if (this.value) {
                            d.set_df_property(
                                'undertaking_content',
                                'options',
                                `<script>function verifyOtp(){
                                    const btn_value = document.getElementById('doc_value');
                                    const otp = document.getElementById('otp');
                                    const otp_area = document.getElementById('otp-area');
                                    
                                    frappe.call({
                                        method:"edu_quality.public.py.undertaking.verify_undertaking_otp",
                                        args: {
                                            "otp": otp.value,
                                            "fee":btn_value.value
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
                                                fee: document.getElementById('doc_value').value,
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
                        }
                        else {
                            d.set_df_property(
                                'undertaking_content',
                                'options',
                                ``);
                        }
                    }
                },
                {
                    fieldtype: "HTML",
                    fieldname: "undertaking_content",
                    label: "",
                    options: html_content
                }
            ],
            size: 'large',
            primary_action_label: 'Submit',
            primary_action: onDialogSubmit
        });

        d.show();

        function showUnderTaking(d) {
            frappe.call({
                method: "edu_quality.edu_quality.server_scripts.manual_payment.get_unpaid_terms",
                type: "POST",
                args: {
                    fee: frm.doc.name,
                    doctype: "Fees",
                    payment_term: d.get_value('payment_term')
                },
                callback: function (response) {
                    undertaking = response.message;
                    console.log(undertaking);
                    if (undertaking.undertaking_enabled) {
                        if (!undertaking.undertaking_accepted) {
                            d.set_df_property('undertaking_check', 'hidden', 0);
                            d.set_df_property('undertaking_check', 'reqd', 1);
                            // hide the submit button if undertaking is not accepted
                            setTimeout(() => {
                                console.log("Delayed for 1 second.");
                                console.log(document.querySelector(".btn-modal-primary"));
                                const x = document.querySelector(".btn-modal-primary");
                                x.style.display = 'none';
                            }, 1000);
                            // Send OTP
                            d.fields_dict.undertaking_check.input.onclick = function () {
                                if (d.fields_dict.undertaking_check.input.checked) {
                                    sendOtp(frm);
                                }
                            };
                        } else {
                            d.set_df_property('undertaking_check', 'hidden', 0);
                            // d.set_df_property('undertaking_check', 'default', 1);
                            d.undertaking_check = 1;
                            d.set_df_property('undertaking_check', 'read_only', 1);
                        }
                    }
                }
            });
        }

        function onDialogSubmit(values) {
            console.log(values)
            if (!values.undertaking_check) {
                frappe.throw("Please select Terms and conditions");
            } else {
                frappe.call({
                    method: "edu_quality.edu_quality.server_scripts.manual_payment.manual_payment",
                    type: "POST",
                    args: { term: values.payment_term, fee: frm.doc.name, data: values.table, payment_mode: values.payment_mode },
                    callback: function (response) {
                        showAlert(response.message, 'green');
                        frm.reload_doc();
                    }
                });
            }
            d.hide();
        }
    }, __("Action"));

    function sendOtp(frm) {
        frappe.call({
            method: "edu_quality.public.py.undertaking.generate_undertaking_otp",
            args: {
                "fee": frm.doc.name,
            },
            callback: function (r) {
                if (r.message === true) {
                    showAlert("OTP has been sent successfully.", 'green');
                }
                else {
                    showAlert("Error while sending OTP.", 'red');
                }
            }
        });
    }

    function showAlert(message, indicator) {
        frappe.show_alert({
            message: __(message),
            indicator: indicator
        });
    }

    async function getPaymentRequest(reference_name, docstatus) {
        let found = false;
        const result = await frappe.db.get_value('Payment Request', { reference_name: reference_name, docstatus: docstatus }, 'name');

        if (result && result.message && result.message.name) {
            found = true;
        }

        return found;
    }

    function getTermAndUnderTaking() {
        // set the unpaid terms and undertaking url and get the undertaking status
        frappe.call({
            method: "edu_quality.edu_quality.server_scripts.manual_payment.get_unpaid_terms",
            type: "POST",
            args: {
                fee: frm.doc.name,
                doctype: "Fees",
            },
            callback: function (response) {
                pdf_url = response.message.undertaking_url
                unpaid_terms = response.message.terms
            }
        });
    }
}


function generate_payment_link(frm) {
    frm.add_custom_button(__("Generate Payment Link"), function () {
        frappe.call({
            doc: frm.doc,
            method: "get_uncreated_payment_terms",
            callback: function (response) {
                let terms = response.message
                let d = new frappe.ui.Dialog({
                    title: 'Generate Payment Link',
                    fields: [
                        {
                            label: 'Payment Term',
                            fieldname: 'payment_term',
                            fieldtype: 'Select',
                            options: terms,
                            reqd: 1
                        }
                    ],
                    size: 'small',
                    primary_action_label: 'Create Link',
                    primary_action(values) {
                        frappe.call({
                            doc: frm.doc,
                            method: "create_payment_request",
                            type: "POST",
                            args: {
                                payment_term: values.payment_term
                            }
                        });
                        d.hide();
                    }
                });
                d.show();
            }
        });
    }, __("Action"));
}

function partial_payment(frm) {
    frm.add_custom_button(__("Partial Payment"), function () {
        let terms = []
        let schedule = frm.doc.payment_schedule
        let total_outstanding = 0

        for (var i in schedule) {
            let term = schedule[i]
            if (term.outstanding > 0) {
                total_outstanding = total_outstanding + term.outstanding
                terms.push({ 'payment_term': term.payment_term, 'amount': term.outstanding, 'due_date': term.due_date })
            }
        }

        let table_fields = [
            { fieldname: "payment_term", fieldtype: "Link", in_list_view: 1, label: "Payment Term", options: "Payment Term", reqd: 1 },
            { fieldname: "due_date", fieldtype: "Date", in_list_view: 1, label: "Due Date", reqd: 1 },
            { fieldname: "amount", fieldtype: "Currency", in_list_view: 1, label: "Amount", reqd: 1 }
        ]

        let d = new frappe.ui.Dialog({
            title: 'Partial Payment',
            size: 'large',
            fields: [
                {
                    label: "Total Outstanding",
                    fieldname: "total_outstanding",
                    fieldtype: "Data",
                    read_only: 1,
                    default: total_outstanding
                },
                {
                    label: "Total Remaining",
                    fieldname: "total_remaining",
                    fieldtype: "Currency",
                    read_only: 1,
                    default: 0
                },
                {
                    fieldtype: 'Table',
                    fieldname: 'table',
                    label: 'Payment Terms',
                    in_place_edit: true,
                    cannot_add_rows: false,
                    reqd: 1,
                    fields: table_fields,
                    data: terms,
                    on_add_row: function (e) {
                        console.log(d)
                        let filled = 0
                        let table = d.fields_dict.table
                        for (let i = 0; i < table.df.data.length; i++) {
                            if (table.df.data[i].amount) {
                                filled = table.df.data[i].amount + filled;
                            }

                        }
                        total = d.fields_dict.total_outstanding.value
                        console.log(total)
                        console.log(filled)
                        d.fields_dict.total_remaining.set_value(total - filled)
                    }
                },
                {
                    fieldtype: 'Section Break',
                    fieldname: "sl"
                },
                {
                    fieldtype: 'Data',
                    fieldname: "otp_entry",
                    label: "OTP",
                    hidden: 1
                },
                {
                    fieldtype: 'Column Break',
                    fieldname: "cl"
                },
                {
                    fieldtype: "Button",
                    fieldname: "verify",
                    label: "Send OTP"
                }
            ],
            primary_action_label: 'Create',
            primary_action(values) {
                frappe.call({
                    doc: frm.doc,
                    method: "create_partial_payment",
                    type: "POST",
                    args: {
                        data: values.table
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint("Partial Pament applied successfully!")
                            frm.reload_doc()
                        }
                    }
                });
                d.hide();
            }
        })

        //hide create button 
        setTimeout(() => {
            const x = document.querySelector(".btn-modal-primary");
            x.style.display = 'none';
        }, 1000);

        d.fields_dict.verify.input.onclick = function () {
            if (d.fields_dict.otp_entry.value) {
                frappe.call({
                    method: "edu_quality.public.py.utils.verify_otp",
                    args: {
                        "fee": frm.doc.name,
                        "otp": values.otp_entry
                    },
                    callback: function (r) {
                        if (r.message === true) {
                            frappe.show_alert({
                                message: __("OTP Verified Successfully"),
                                indicator: 'green'
                            });
                            setTimeout(() => {
                                const x = document.querySelector(".btn-modal-primary");
                                x.style.display = 'block';
                            }, 1000);
                        } else {
                            frappe.show_alert({
                                message: __("Invalid OTP, Please try again"),
                                indicator: 'red'
                            });
                        }
                    }
                });
            }
            else {
                d.fields_dict.otp_entry.df.hidden = 0
                d.fields_dict.otp_entry.refresh()
                d.fields_dict.verify.df.label = "Verify OTP"
                d.fields_dict.verify.refresh()


                frappe.call({
                    method: "edu_quality.public.py.utils.generate_otp",
                    args: {
                        fee: frm.doc.name,
                        undertaking: 1
                    },
                    callback: function (r) {
                        if (r.message === true) {
                            showAlert("OTP has been sent successfully.", 'green');
                        }
                        else {
                            showAlert("Error while sending OTP.", 'red');
                        }
                    }
                });
            }
        }
        d.show();
    }, __("Action"));
}