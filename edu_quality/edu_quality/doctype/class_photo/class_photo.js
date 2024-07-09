async function folderExists(parent, newFolder) {
    const formData = new FormData()
    formData.append('file_name', newFolder)
    formData.append('folder', parent)

    try {
        let googleRes = await fetch(`/api/method/edu_quality.edu_quality.doctype.class_photo.class_photo.check_folder_in_drive`, {
            method: 'POST',

            headers: (() => {
                const headers = new Headers()
                headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
                headers.append('Content-Type', 'application/json')
                headers.append('Accept', 'application/json')
                return headers;
            })(),
            body: JSON.stringify({ 'folder_name': newFolder })
        });

        let res = await fetch(`/api/resource/File/${parent}/${newFolder}`)
        if (res.status === 404) {
            await fetch("/api/method/frappe.core.api.file.create_new_folder", {
                method: 'POST',
                headers: (() => {
                    const headers = new Headers()
                    headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
                    return headers;
                })(),
                body: formData
            })
        }
        return (await res.json())

    } catch (e) {
        console.error(e)
    }

}


frappe.ui.form.on("Class Photo", {
    refresh: function (frm) {
        console.log(frm)
        setTimeout(() => {
            if (!frm.doc.__islocal) {
                var element = frm.add_custom_button(__("Upload Images"), async function () {
                    await folderExists('Home', frm.doc.name)
                    try {
                        const images = await nativeInterface.execute('openWebViewCamera', {
                            multiple: true,
                            preferredCameraType: 'rear',
                            galleryTitle: frm.doc.name,
                            backgroundMode: true,
                            endpoint: "edu_quality.edu_quality.doctype.class_photo.class_photo.move_existing_and_upload_to_drive",
                            parameters: {
                                "method": "POST",
                                "folder_name": `${frm.doc.name}`,
                            },

                        })
                        frappe.msgprint({
                            title: __('Successful'),
                            message: __('Upload Started, restarting app will restart unfinished uploads'),

                        })
                    }
                    catch (e) {
                        nativeInterface.logToNative(e)
                    }



                }).addClass('btn-primary')
                element.addClass('btn-primary')
                element.parent().removeClass('hidden-xs hidden-md')
            }
        })
    },
    school: function (frm) {
        frm.set_query("class", function () {
            return {
                "filters": {
                    "school": frm.doc.school,


                }
            };
        })

    },
    class: function (frm) {
        frm.set_query("division", function () {
            return {
                "filters": {
                    "custom_school": frm.doc.school,
                    "program": frm.doc.class

                }
            };
        })
    }

});
