// Copyright (c) 2024, Hybrowlabs Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Birthday Card", {
    refresh(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button("Take Photos", async () => {
                const images = await nativeInterface.execute('openWebViewCamera', {
                    multiple: true,
                    preferredCameraType: 'rear',
                    galleryTitle: frm.doc.name,
                    backgroundMode: false,

                })

            })
            frm.add_custom_button("Print Birthday Card", async function () {
                let pdfUrl
                try {
                    const headers = new Headers()
                    headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
                    headers.append('Content-Type', 'application/json')
                    const payload = { "birthday_card": frm.doc.name, type: "POST" }
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
    },
});
