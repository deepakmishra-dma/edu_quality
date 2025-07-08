frappe.ui.form.on("Program", {
    refresh: function (frm) {
        frm.add_custom_button(__("Shuffle Division"), function () {
            shuffleDivision(frm);
        }).addClass("btn-primary");
    }
});

async function shuffleDivision(frm) {
    let data = await getDivisionMessage(frm)

    var dialog = new frappe.ui.Dialog({
        title: 'Shuffle Division',
        fields: [
            {
                fieldtype: 'Button',
                label: 'Export Student Details',
                fieldname: 'export',
                click: function () {
                    frappe.call({
                        method: 'edu_quality.api.student.export_student_details',
                        args: {
                            program: frm.doc.name,
                        },
                        callback: function(response) {
                            var a = document.createElement('a');
                            var filecontent = atob(response.message.filecontent);
                            var blob = new Blob([filecontent], {type: 'application/csv'});
                            var url = window.URL.createObjectURL(blob);
                            a.href = url;
                            a.download = response.message.filename;
                            document.body.append(a);
                            a.click();
                            a.remove();
                            window.URL.revokeObjectURL(url);
                        }
                    });
                }
            },
            {
                fieldtype: 'HTML',
                label: 'Details',
                fieldname: 'details',
                options: data
            }
        ],
        size: 'large',
        primary_action_label: 'Okay',
        primary_action: function () {
            frappe.call({
                method: 'edu_quality.api.student.shuffle_division_data',
                args: {
                    program: frm.doc.name,
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __(r.message),
                            indicator: 'green'
                        });
                    }
                }
            });
            dialog.hide();
        }
    });

    dialog.show();
}

async function getDivisionMessage(frm) {
    const data = await frappe.call({
        method: 'edu_quality.api.student.get_student_details',
        args: {
            program: frm.doc.name,
        }
    });

    data.message = Object.keys(data.message).sort().reduce(
        (obj, key) => {
            obj[key] = data.message[key];
            return obj;
        },
        {}
    );

    const html_content = Object.keys(data.message).map(key => {
        const details = data.message[key];
        return `
            <details>
                <summary>${key}</summary>
                <p>Total Students: ${details.no_of_students}</p>

                <div style="display: grid; grid-template-columns: 1fr 1fr;">
                    <p>Boys: ${details.boys}</p>
                    <p>Girls: ${details.girls}</p>
                    <p>Yellow: ${details.yellow}</p>
                    <p>Green: ${details.green}</p>
                    <p>Red: ${details.red}</p>
                    <p>Blue: ${details.blue}</p>
                </div>
                <details>
                    <summary>Students</summary>
                    <div style="display: grid; grid-template-columns: 1fr 1fr;">
                        ${details.students.map(student => {
                            return `<p>${student.name}: ${student.first_name}-${student.school_house}</p>`;
                        }).join('')}
                    </div>
                </details>
            </details>
        `;
    }).join('');

    return `<div style="display: grid; grid-template-columns: 1fr 1fr;">${html_content}</div>`;
}