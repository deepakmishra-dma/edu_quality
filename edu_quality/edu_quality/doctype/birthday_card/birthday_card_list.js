// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.listview_settings["Birthday Card"] = {
    refresh: function(listview) {
        listview.page.add_action_item(__("Print Birthday Cards"), async function () {
            const selectedBirthdayCards = listview?.get_checked_items(true);

            let pdfUrl
            try {
                const headers = new Headers()
                headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
                headers.append('Content-Type', 'application/json')
                const payload = { "birthday_cards": selectedBirthdayCards, type: "POST" }
                const generated = await fetch(`/api/method/edu_quality.edu_quality.doctype.birthday_card.birthday_card.print_birthday_card`, {
                    method: 'POST',
                    headers: headers, body: JSON.stringify(payload)
                })
                const file = await generated.blob()
                pdfUrl = URL.createObjectURL(file);
                window.open(pdfUrl, '_blank');
            } catch (e) {
                console.error(e)
            }
            finally {
                if (pdfUrl) {
                    URL.revokeObjectURL(pdfUrl)
                }
            }
        })
    }
}
