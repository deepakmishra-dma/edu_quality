// make child table read only if current user role is student
frappe.ui.form.on("Student", {
    refresh: function (frm) {
        if (frappe.user.has_role("Student")) {
            frm.set_df_property("class_details", "read_only", 1);
        }
        addFeeDetails(frm);
        addParentDetails(frm);
        addReferral(frm);
    },

    late_drop: function (frm) {
        frappe.call({
            method: "edu_quality.edu_quality.server_scripts.student.mark_entry",
            args: {
                student: frm.selected_doc.name,
                reason: frm.selected_doc.reason,
                status: "Late Drop"
            },
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __("Marked Entry!"),
                        indicator: 'green'
                    });
                }
                else{
                    frappe.show_alert({
                        message: __("Something went wrong!"),
                        indicator: 'red'
                    });

                }
                d.hide();
            }
        });
    },
    early_pickup: function (frm) {
        frappe.call({
            method: "edu_quality.edu_quality.server_scripts.student.mark_entry",
            args: {
                student: frm.selected_doc.name,
                reason: frm.selected_doc.reason,
                status: "Early Pickup"
            },
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __("Marked Entry!"),
                        indicator: 'green'
                    });
                }
                else{
                    frappe.show_alert({
                        message: __("Something went wrong!"),
                        indicator: 'red'
                    });

                }
                d.hide();
            }
        });
    }
});


function addReferral(frm){
    frm.add_custom_button(__('Add Referral'), function () {
        let d = new frappe.ui.Dialog({
            title: 'Add Referral',
            fields: [
                {
                    label: 'Referred Student',
                    fieldname: 'referred_student',
                    fieldtype: 'Link',
                    options: "Student",
                    get_query: function () {
                        return {
                            doctype: 'Student',
                            filters: [["Student","referred_by","is","not set"]],
                        };
                    }
                }
            ],
            size: 'large',
            primary_action_label: 'Submit',
            primary_action(values) {
                frappe.call({
                    method: "edu_quality.edu_quality.server_scripts.utils.add_referral",
                    type: "POST",
                    args: {
                        referred_student: values.referred_student,
                        referred_by: frm.doc.name
                    },
                    callback: function (response) {
                        if(response.message==1){
                        frappe.show_alert({
                            message: __("Referral Added"),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                    else{
                        frappe.show_alert({
                            message: __("Something Went Wrong!"),
                            indicator: 'red'
                        });
                    }
                        
                    }
                });
                d.hide();
            }
        });

        d.show();

    });
}

function addFeeDetails(frm) {
    if(!frm.is_new()){
        frappe.call({
            method: "edu_quality.public.py.student.get_fees_details",
            args: {
                student: frm.selected_doc.name
            },
            callback: function (r) {
                if (r.message) {
                    const data = r.message.map((item, index) => {
                        const { payment_term, description, due_date, invoice_portion, payment_amount, paid_date, parent, doctype } = item;
                        let link = doctype == 'Fee Advance' ? `/app/fee-advance/${parent}` : `/app/fees/${parent}`;
                        return `
                            <tr>
                                <td>${index + 1}</td>
                                <td>${payment_term}</td>
                                <td>${description}</td>
                                <td>${due_date}</td>
                                <td>${invoice_portion}</td>
                                <td>${payment_amount}</td>
                                <td>${paid_date ? paid_date : 'Not Paid'}</td>
                                <td><a href="${link}">Open</a></td>
                            </tr>`;
                    }).join('');

                    frm.$wrapper[0].querySelector("#fees").innerHTML = data ? `
                    <table class="table table-bordered">
                        <tr>
                            <th>Sr.No</th>
                            <th scope="col">Payment Term</th>
                            <th scope="col">Description</th>
                            <th scope="col">Due Date</th>
                            <th scope="col">Invoice Portion</th>
                            <th scope="col">Payment Amount</th>
                            <th scope="col">Paid Date</th>
                            <th scope="col">Action</th>
                        </tr>
                        ${data}
                    </table>` : `<center><p> There is no current record</p></center>`;
                }
            }
        });
    }
}

function addParentDetails(frm){
    if(!frm.is_new()){
        frappe.call({ 
            method: "edu_quality.public.py.student.get_parents_details",
            args: {
                student: frm.selected_doc.name 
            },
            callback: function(r) {
                let data = '';
                if(r.message){
                    r.message.forEach((item, index) => {
                        console.log(item);
                        data += `<tr>
                            <td>${index + 1}</td>
                            <td>${item['guardian_name']}</td>
                            <td>${item['relation']}</td>
                            <td>${item['mobile_number']}</td>
                            <td>${item['email_address']}</td>
                            <td>${item['occupation']}</td>
                            <td>${item['annual_income']}</td>
                            <td>${item['work_address']}</td>
                            <td><a href="/app/guardian/${item['name']}">Open</a></td>
                        </tr>`;
                    });

                    if (data){
                        frm.$wrapper[0].querySelector("#parents").innerHTML = `
                        <table class="table table-bordered">
                            <tr>
                                <th>Sr.No</th>
                                <th scope="col">Parent Name</th>
                                <th scope="col">Relation</th>
                                <th scope="col">Phone</th>
                                <th scope="col">Email</th>
                                <th scope="col">Occupation</th>
                                <th scope="col">Annual Income</th>
                                <th scope="col">Address</th>
                                <th scope="col">More Details</th>
                            </tr>
                            <tr>
                                ${data}
                            </tr>
                        </table>`;
                    }
                }
                else {
                    frm.$wrapper[0].querySelector("#parents").innerHTML = `<center><p> There is no current record</p></center>`;
                }
            }
        });
    }
}