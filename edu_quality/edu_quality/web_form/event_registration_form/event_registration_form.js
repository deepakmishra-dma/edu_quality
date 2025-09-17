frappe.ready(function() {
    document.title = "Event Registration Form";

    // Attach event listener to form submit
    var button = document.createElement("button");
    button.innerHTML = "Confirm Registration";

    // Add Bootstrap classes to the button
    button.className = "btn btn-primary";

    // Append the button to the form
    var form = document.getElementsByTagName("form")[0];
    form.appendChild(button);

    // Add event listener for the click event of the button
    button.addEventListener("click", async function(event) {
        event.preventDefault();
		let doc = frappe.reference_doc;

        frappe.call({
            method: "edu_quality.edu_quality.doctype.event_detail.event_detail.add_participating_students",
            args: {
				student_data: doc,
			},
            callback: function(response) {
                if (response.message) {
					frappe.show_alert("Registration Successful", 5);
                }else{
                    frappe.show_alert("Already Registered", 5);
                }
            }
        });
    });
});
