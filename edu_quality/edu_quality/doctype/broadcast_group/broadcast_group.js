// Copyright (c) 2023, Hybrowlabs Technologies and contributors
// For license information, please see license.txt
const handleTemplateBroadcast = async (messsageToSend) => {
	const headers = new Headers()
	headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
	headers.append('content', 'application/json')
	try {
		const messageCreatedRes = await fetch("/api/resource/WhatsApp Message", {
			headers: headers,
			method: "POST",
			body: JSON.stringify(messsageToSend)
		})
		const messageCreatedMsg = await messageCreatedRes.json()
		if (messageCreatedRes.status === 500 || messageCreatedRes.status === 417 || messageCreatedRes.status === 400) {
			throw messageCreatedMsg
		}

		const body = `docs=${encodeURIComponent(
			JSON.stringify(messageCreatedMsg?.data)
		)}&method=send`;

		const ranSuccessfully = await fetch(`/api/method/run_doc_method?${body}`, {
			method: "POST",
			headers: headers,
			body: body,
		});

		const data = await ranSuccessfully.json()
		if (ranSuccessfully.status !== 200) {
			throw data
		}
	}
	catch (e) {
		return Promise.reject(e)
	}

}
frappe.ui.form.on('Broadcast Group', {
	// refresh: function(frm) {

	// }
	refresh: function (frm) {
		frm.add_custom_button(__("Broadcast Message"), async function () {
			const templates = await (await fetch('/api/resource/WhatsApp Template')).json()
			const mappedTemplates = templates?.data?.map((template) => { return template.name })
			const whatsappTemplate = new frappe.ui.Dialog({
				title: "Select a Whatsapp Template",
				fields: [
					{
						fieldtype: "Select",
						label: "Name",
						fieldname: "group_name",
						reqd: true,
						options: mappedTemplates

					},
				],
				size: "small",
				primary_action_label: "Create",

				primary_action: async function (values) {
					try {
						const templateReactDialog = document.createElement("whatsapp-template")
						templateReactDialog.templateName = values.group_name;
						templateReactDialog.hideCloseButton = true
						// document.body.appendChild(el)
						const templateDialog = new frappe.ui.Dialog({
							title: "Enter template content",
							fields: [
								{
									fieldtype: "HTML",
									fieldname: "render_html",
								}
							]
						})
						templateReactDialog.sendFallback = async (_, message) => {

							try {
								const messages = frm.doc.group_members?.map((memberDoc) => {
									const a = frappe.model.get_doc("Lead", memberDoc?.member_name)
									return { ...message, to: memberDoc.contact_doc }
								})

								const sentAll = await Promise.all(messages.map(handleTemplateBroadcast))
								frappe.msgprint({
									title: __('Successful'),
									message: __('Queued All'),

								})
							}
							catch (e) {
								frappe.msgprint({
									title: __('Error'),
									message: __('Something Went Wrong'),

								})
							}
							finally {
								templateDialog.hide()
							}

						}
						templateDialog.fields_dict.render_html.$wrapper.html(templateReactDialog);
						whatsappTemplate.hide()
						templateDialog.show()
					}
					catch (e) {

						console.error(e)
					}

				},
			});

			whatsappTemplate.show()
		})
	},
});
