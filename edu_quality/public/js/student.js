// make child table read only if current user role is student
frappe.ui.form.on("Student", {
    refresh: function (frm) {
        if (frappe.user.has_role("Student")) {
            frm.set_df_property("class_details", "read_only", 1);
        }
        addFeeDetails(frm);
        addParentDetails(frm);
    }
});

function addFeeDetails(frm) {
    frappe.call({
        method: "edu_quality.public.py.student.get_fees_details",
        args: {
            student: frm.selected_doc.name
        },
        callback: function (r) {
            if (r.message) {
                const data = r.message.map((item, index) => {
                    const { payment_term, description, due_date, invoice_portion, payment_amount, paid_date, parent } = item;
                    return `
                        <tr>
                            <td>${index + 1}</td>
                            <td>${payment_term}</td>
                            <td>${description}</td>
                            <td>${due_date}</td>
                            <td>${invoice_portion}</td>
                            <td>${payment_amount}</td>
                            <td>${paid_date ? paid_date : 'Not Paid'}</td>
                            <td><a href="/app/fees/${parent}">Open</a></td>
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

function addParentDetails(frm){
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