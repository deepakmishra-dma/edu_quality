frappe.listview_settings['Program Enrollment'] = {

    onload: function (list_view) {
        list_view.page.add_action_item("Generate Permanent ID Cards", async () => {
            const selectedEnrollments = list_view?.get_checked_items(true);

            let pdfUrl
            try {

                const payload = { "enrollments": selectedEnrollments, type: "POST" }

                const generated = await frappe.call({

                    method: `edu_quality.api.print_id_card.generate_permanent_id_cards`,
                    args: payload
                })

                if (generated?.message === "Enqueued Successfully")
                    frappe.msgprint({
                        title: __("ID Card Generation"),
                        message: __('Permanent ID Cards Generation Scheduled Successfully. <a href="/app/permanent-id-card" target="_blank">Click Here</a>'),
                        primary_action: {
                            label: __("OK"),
                            action: function () {
                                frappe.hide_msgprint();
                            }
                        }
                    });
            }

            catch (e) {
                console.error(e)
                throw e
            }
            finally {
                if (pdfUrl) {
                    URL.revokeObjectURL(pdfUrl)
                }
            }
        });
        list_view.page.add_action_item("Generate Temporary ID Cards", async () => {
            const selectedEnrollments = list_view?.get_checked_items(true);

            let pdfUrl
            try {
                const headers = new Headers()
                headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
                headers.append('Content-Type', 'application/json')
                const payload = { "enrollments": selectedEnrollments, type: "POST" }
                console.log(payload, 'xx')
                const generated = await fetch(`/api/method/edu_quality.api.print_id_card.generate`, {
                    method: 'POST',

                    headers: headers, body: JSON.stringify(payload)
                })
                const file = await generated.blob()
                pdfUrl = URL.createObjectURL(file);
                window.open(pdfUrl, '_blank');


            }

            catch (e) {
                console.error(e)

            }
            finally {
                if (pdfUrl) {
                    URL.revokeObjectURL(pdfUrl)
                }

            }


        });
        frappe.db.get_list("Academic Year", { filters: { "custom_current_academic_year": 1 }, fields: ["name"] }).then((response) => {
            if (!frappe.route_options) {
                const result = response?.[0]?.name
                frappe.listview_settings['Program Enrollment']["filters"] = [["academic_year", "=", result]]
            }
        })


    }
}