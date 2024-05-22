// make child table read only if current user role is student
frappe.ui.form.on("Student", {
    refresh: function (frm) {
        if (frappe.user.has_role("Student")) {
            frm.set_df_property("class_details", "read_only", 1);
        }
        frappe.call({ 
            method: "edu_quality.public.py.student.get_fees_details",
            args: {
                student: frm.selected_doc.name 
            },
            callback: function(r) {
                let data = ''
                if(r.message){
                    let result = r.message
                    for (var i = 0; i <= result.length - 1; i++) {
                        let temp = result[i]['parent']
                        data +=
                            `<tr>
                            <td>`+ (i + 1) + `</td>
                            <td>` + result[i]['payment_term'] + `</td>
                            <td>` + result[i]['description'] + `</td>
                            <td>` + result[i]['due_date'] + `</td>
                            <td>` + result[i]['invoice_portion'] + `</td>
                            <td>` + result[i]['payment_amount'] + `</td>
                            <td><a href="/app/fees/${temp}">Open</a></td>
                        </tr>`
                    }
                }
                if (data) {
                    frm.$wrapper[0].querySelector("#fees").innerHTML = `
                    <table class="table table-bordered">
                        <tr>
                            <th>Sr.No</th>
                            <th scope="col">Payment Term</th>
                            <th scope="col">Description</th>
                            <th scope="col">Due Date</th>
                            <th scope="col">Invoice Portion</th>
                            <th scope="col">Payment Amount</th>
                            <th scope="col">Action</th>
                        </tr>
                        <tr>
                            `+ data + `
                        </tr>
                        
                    </table>`
                }
                else {
                    frm.$wrapper[0].querySelector("#fees").innerHTML = `<center><p> There is no current record</p></ceneter>`
                }
            }})





    }
});
