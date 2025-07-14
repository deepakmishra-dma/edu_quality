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
        }
    },
});
