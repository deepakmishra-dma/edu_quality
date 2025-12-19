// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Event Participant", {
//     refresh(frm) {
//         showParticipantDetails(frm);
//     },
// });

function titleCase(str) {
    return str.toLowerCase().split(' ').map(function (word) {
        return (word.charAt(0).toUpperCase() + word.slice(1));
    }).join(' ');
}


function showParticipantDetails(frm) {
    if (!frm.is_new()) {
        const container = frm.$wrapper[0].querySelector("#participant_details");
        if (frm.doc.data) {
            let data = JSON.parse(frm.doc.data);
            const tableRows = Object.entries(data).map(([key, value]) => {
                return `
                    <tr>
                    <td>${titleCase(key.replace("_", " "))}</td>
                    <td>${value}</td>
                    </tr>
                `;
            }).join("");

            container.innerHTML = `
                <h3>Participant Details</h3>
                <table class="table table-bordered">
                    <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Data</th>
                    </tr>
                    </thead>
                    <tbody>
                    ${tableRows}
                    </tbody>
                </table>
                `;
        }
    }
}
