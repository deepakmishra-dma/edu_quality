// make child table read only if current user role is student
frappe.ui.form.on("Student", {
    refresh: function (frm) {
        if (frappe.user.has_role("Student")) {
            frm.set_df_property("class_details", "read_only", 1);
        }
        addFeeDetails(frm);
        addDepositDetails(frm);
        addHDTicketDetails(frm);
        addParentDetails(frm);
        addReferral(frm);
        swapDivisionButton(frm);
        cancelStudent(frm);
        // changeClass(frm);
    },

    custom_late_drop: markLateDrop,
    custom_early_pickup: markEarlyPickup,
    late_drop: markLateDrop,
    early_pickup: markEarlyPickup
});
function markLateDrop(frm) {

    frappe.call({
        method: "edu_quality.edu_quality.server_scripts.student.mark_entry",
        args: {
            student: frm.selected_doc.name,
            reason: frm.selected_doc.custom_reason,
            status: "Late Drop"
        },
        callback: function (r) {
            if (r.message) {
                frappe.show_alert({
                    message: __("Marked Entry!"),
                    indicator: 'green'
                });
            }
            else {
                frappe.show_alert({
                    message: __("Something went wrong!"),
                    indicator: 'red'
                });

            }

        }
    });
}

function markEarlyPickup(frm) {
    frappe.call({
        method: "edu_quality.edu_quality.server_scripts.student.mark_entry",
        args: {
            student: frm.selected_doc.name,
            reason: frm.selected_doc.custom_reason,
            status: "Early Pickup"
        },
        callback: function (r) {
            if (r.message) {
                frappe.show_alert({
                    message: __("Marked Entry!"),
                    indicator: 'green'
                });
            }
            else {
                frappe.show_alert({
                    message: __("Something went wrong!"),
                    indicator: 'red'
                });

            }

        }
    });
}
function cancelStudent(frm) {
    if (frm.doc.student_status == "Cancelled") {
        return 1
    }
    frm.add_custom_button(__('Cancel Student'), function () {

        frappe.call({
            doc: frm.doc,
            async: true,
            freeze: true,
            method: "create_student_exit",
            callback: function (r) {
                if (r.message) {
                    window.location = "/app/student-exit/" + frm.doc.name;
                }
                else {
                    frappe.show_alert({
                        message: __("Something went wrong!"),
                        indicator: 'red'
                    });
                }
            }
        });
    }, __("Action"));

}


function addReferral(frm) {
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
                            filters: [["Student", "referred_by", "is", "not set"]],
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
                        if (response.message == 1) {
                            frappe.show_alert({
                                message: __("Referral Added"),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                        else {
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

    }, __("Action"));
}

function addFeeDetails(frm) {
    if (!frm.is_new()) {
        frappe.call({
            doc: frm.doc,
            method: "get_fees_details",
            args: {
                student: frm.selected_doc.name
            },
            callback: function (r) {
                if (r.message) {
                    const data = r.message.map((item, index) => {
                        const { payment_term, description, due_date, invoice_portion, payment_amount, outstanding, parent, doctype, paid_date } = item;
                        let link = doctype == 'Fee Advance' ? `/app/fee-advance/${parent}` : `/app/fees/${parent}`;
                        return `
                            <tr>
                                <td>${index + 1}</td>
                                <td>${payment_term}</td>
                                <td>${description}</td>
                                <td>${due_date}</td>
                                <td>${invoice_portion}</td>
                                <td>${payment_amount}</td>
                                <td>${outstanding == 0 ? `${paid_date}` : 'Not Paid'}</td>
                                <td><a href="${link}">Open</a></td>
                            </tr>`;
                    }).join('');

                    frm.$wrapper[0].querySelector("#fees").innerHTML = data ? `
                    <h4> Fee Details </h4>
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

function addDepositDetails(frm) {
    if (!frm.is_new()) {
        frappe.call({
            doc: frm.doc,
            method: "get_deposit_details",
            callback: function (r) {
                if (r.message) {
                    const data = r.message.map((item, index) => {
                        const { name, posting_date, paid_amount } = item;
                        return `
                            <tr>
                                <td>${index + 1}</td>
                                <td>${posting_date}</td>
                                <td>${paid_amount}</td>
                                <td><a href="/app/payment-entry/${name}" target='_blank'>Open</a></td>
                            </tr>`;
                    }).join('');

                    frm.$wrapper[0].querySelector("#deposit").innerHTML = data ? `
                    <h4> Deposit Details </h4>
                    <table class="table table-bordered">
                        <tr>
                            <th>Sr.No</th>
                            <th scope="col">Paid Date</th>
                            <th scope="col">Payment Amount</th>
                            <th scope="col">Action</th>
                        </tr>
                        ${data}
                    </table>` : `<center><p> There is no current record</p></center>`;
                }
            }
        });
    }
}

function addHDTicketDetails(frm) {
    if (!frm.is_new()) {
        frappe.call({
            doc: frm.doc,
            method: "get_hd_ticket_details",
            callback: function (r) {
                if (r.message) {
                    const data = r.message.map((item) => {
                        const { name, subject,  status } = item;
                        return `
                            <tr>
                                <td>${name}</td>
                                <td>${subject}</td>
                                <td>${status}</td>
                                <td><a href="/app/hd-ticket/${name}" target='_blank'>Open</a></td>
                            </tr>`;
                    }).join('');
                    console.log('data',data);

                    frm.$wrapper[0].querySelector("#tickets").innerHTML = data ? `
                    <h4> Helpdesk Tickets </h4>
                    <table class="table table-bordered">
                        <tr>
                            <th scope="col">Ticket ID</th>
                            <th scope="col">Subject</th>
                            <th scope="col">Status</th>
                            <th scope="col">Action</th>
                        </tr>
                        ${data}
                    </table>` : `<center><p>No Tickets found</p></center>`;
                }else{
                    frm.$wrapper[0].querySelector("#tickets").innerHTML = `<center><p>No Tickets found</p></center>`;
                }
            }
        });
    }
}

function addParentDetails(frm) {
    if (!frm.is_new()) {
        frappe.call({
            method: "edu_quality.public.py.student.get_parents_details",
            args: {
                student: frm.selected_doc.name
            },
            callback: function (r) {
                let data = '';
                if (r.message) {
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

                    if (data) {
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


function swapDivisionButton(frm) {
    frm.add_custom_button(__('Swap/Change Division'), async function () {
        let cur_ay = await frappe.db.get_value('Academic Year', { custom_current_academic_year: 1 }, ['name']);
        let cur_pe = await frappe.db.get_value('Program Enrollment', { student: frm.doc.name, program: frm.doc.program, academic_year: cur_ay.name, docstatus: 1 }, ['name', 'student_group']);
        if (!cur_pe.message || Object.keys(cur_pe.message).length === 0) {
            frappe.msgprint({
                title: __("Program Enrollment Error"),
                message: __('Program Enrollment not found for this student! for current academic year. Please check and try again.'),
                primary_action: {
                    label: __("OK"),
                    action: function () {
                        frappe.hide_msgprint();
                    }
                }
            });
            return;
        }
        let division = cur_pe.message.student_group.split('-')[0];
        let cur_batch = await frappe.db.get_value('Student Group', { "name": cur_pe.message.student_group }, "batch")
        let d = new frappe.ui.Dialog({
            title: 'Swap/Change Division',
            fields: [
                {
                    label: 'Swap With Student',
                    fieldname: 'student_check',
                    fieldtype: 'Check',
                    default: 0,
                    onchange: function () {
                        if (d.get_value('student_check')) {
                            d.set_df_property('student', 'hidden', 0);
                            d.set_df_property('division', 'hidden', 1);
                        } else {
                            d.set_df_property('student', 'hidden', 1);
                            d.set_df_property('division', 'hidden', 0);
                        }
                    }
                },
                {
                    label: 'Division',
                    fieldname: 'division',
                    fieldtype: 'Link',
                    options: "Student Group",
                    get_query: function () {
                        return {
                            doctype: 'Student Group',
                            filters: [["program", "=", frm.doc.program], ["academic_year", "=", cur_ay.message.name], ["name", "!=", cur_pe.message.student_group], ["disabled", "=", 0]],
                        };
                    }
                },
                {
                    label: 'Student',
                    fieldname: 'student',
                    fieldtype: 'Link',
                    options: "Student",
                    hidden: 1,
                    get_query: function () {
                        return {
                            doctype: 'Student',
                            filters: [["program", "=", frm.doc.program], ["name", "!=", frm.doc.name], ["custom_division", "!=", division]],
                        };
                    }
                }
            ],
            size: 'large',
            primary_action_label: 'Submit',
            primary_action: async function (values) {
                let new_batch = await frappe.db.get_value('Student Group', { "name": values.division }, "batch");

                if (cur_batch.message.batch == new_batch.message.batch) {
                    swapDivision(frm, values.student, cur_pe.message.name, values.division);
                } else {
                    frappe.confirm('Change in batches, Are you sure you want to proceed?',
                        () => { swapDivision(frm, values.student, cur_pe.message.name, values.division); },
                        () => {
                            frappe.show_alert({
                                message: __("Action Cancelled"),
                                indicator: 'orange'
                            });
                        }
                    )
                }
                d.hide();
            }
        });

        d.show();

    }, __("Action"));
}

function swapDivision(frm, student, program_enrollment, division) {
    frappe.call({
        method: "edu_quality.edu_quality.server_scripts.student.swap_division",
        type: "POST",
        args: {
            program_enrollment: program_enrollment,
            division: division,
            student_to_swap: student,
        },
        callback: function (response) {
            if (response.message) {
                frappe.show_alert({
                    message: __("Division Swapped"),
                    indicator: 'green'
                });
                frm.reload_doc();
            }
            else {
                frappe.show_alert({
                    message: __("Something Went Wrong! Please check Error log"),
                    indicator: 'red'
                });
            }
        }
    });
}


function changeClass(frm) {
    frm.add_custom_button(__('Change Class'), function () {
        let d = new frappe.ui.Dialog({
            title: 'Change Class',
            fields: [
                {
                    label: 'School',
                    fieldname: 'school',
                    fieldtype: 'Link',
                    options: "School",
                    reqd: 1,
                    default: frm.doc.school,
                },
                {
                    label: 'Class',
                    fieldname: 'class',
                    fieldtype: 'Link',
                    options: "Program",
                    default: frm.doc.program,
                    reqd: 1,
                    get_query: function () {
                        return {
                            doctype: 'Program',
                            filters: [["school", "=", d.get_value('school')]],
                        };
                    }
                },
                {
                    label: 'Division',
                    fieldname: 'division',
                    fieldtype: 'Link',
                    options: "Student Group",
                    default: frm.doc.custom_division + "-" + frm.doc.program,
                    reqd: 1,
                    get_query: function () {
                        return {
                            doctype: 'Student Group',
                            filters: [["program", "=", d.get_value('class')], ["academic_year", "=", frm.doc.custom_academic_year]],
                        };
                    }
                },
            ],
            size: 'large',
            primary_action_label: 'Submit',
            primary_action(values) {
                frappe.call({
                    doc: frm.doc,
                    method: "change_class",
                    type: "POST",
                    args: {
                        school: values.school,
                        program: values.class,
                        division: values.division
                    },
                    callback: function (response) {
                        if (response.message == 1) {
                            frappe.show_alert({
                                message: __("Class Change Successful!"),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                        else {
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
    }, __("Action"));
}