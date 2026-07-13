async function folderExists(parent, newFolder) {
  const formData = new FormData();
  formData.append("file_name", newFolder);
  formData.append("folder", parent);

  try {
    let googleRes = await fetch(
      `/api/method/edu_quality.edu_quality.doctype.carnival_event.carnival_event.check_folder_in_drive`,
      {
        method: "POST",

        headers: (() => {
          const headers = new Headers();
          headers.append("X-Frappe-CSRF-Token", frappe.csrf_token);
          headers.append("Content-Type", "application/json");
          headers.append("Accept", "application/json");
          return headers;
        })(),
        body: JSON.stringify({ folder_name: newFolder }),
      }
    );
    let res = await fetch(`/api/resource/File/${parent}/${newFolder}`);
    if (res.status === 404) {
      await fetch("/api/method/frappe.core.api.file.create_new_folder", {
        method: "POST",
        headers: (() => {
          const headers = new Headers();
          headers.append("X-Frappe-CSRF-Token", frappe.csrf_token);
          return headers;
        })(),
        body: formData,
      });
    }
    return await res.json();
  } catch (e) {
    console.error(e);
  }
}

function uploadToGoogleDrive(file_url, folder_name) {
  return fetch(
    "/api/method/edu_quality.edu_quality.doctype.google_drive_settings.google_drive_settings.upload_file",
    {
      method: "POST",
      headers: (() => {
        const headers = new Headers();
        headers.append("X-Frappe-CSRF-Token", frappe.csrf_token);
        return headers;
      })(),
      body: formData,
    }
  );
}

async function uploadImage(image, frm) {
  return fetch(image)
    .then((res) => res.blob())
    .then((blob) => {
      const formData = new FormData();
      const file = new File([blob], "image.jpg");

      formData.append("file", file, "image.jpg");
      formData.append("folder", "home/" + frm.doc.name);
      formData.append("file_name", `${frm.doc.name}-${Date.now()}`);

      nativeInterface.logToNative(formData);
      return fetch("/api/method/upload_file", {
        method: "POST",
        headers: (() => {
          const headers = new Headers();
          headers.append("X-Frappe-CSRF-Token", frappe.csrf_token);
          return headers;
        })(),
        body: formData,
      });
    })
    .then((res) => {
      return res.json();
    })
    .then(({ message }) => message.file_url)
    .catch((error) => {
      nativeInterface.logToNative(error);
    });
}

frappe.ui.form.on("Carnival Event", {
  refresh: function (frm) {
    console.log(frm);
    setTimeout(() => {
      if (!frm.doc.__islocal) {
        var element = frm
          .add_custom_button(__("Upload Images"), async function () {
            await folderExists("Home", frm.doc.name);
            try {
              const images = await nativeInterface.execute(
                "openWebViewCamera",
                {
                  multiple: true,
                  preferredCameraType: "rear",
                  galleryTitle: frm.doc.name,
                  backgroundMode: true,
                  endpoint:
                    "edu_quality.edu_quality.doctype.carnival_event.carnival_event.move_existing_and_upload_to_drive",
                  parameters: {
                    method: "POST",
                    folder_name: `${frm.doc.name}`,
                  },

                  // backgroundStorageKey: "Carnival Events"
                }
              );

              // const imageUrls = await Promise.allSettled(images.map((img) => uploadImage('data:image/jpg;base64,' + img.base64, frm)))
              // imageUrls.map((img) => frappe.call({
              //     method: "edu_quality.api.google_drive_upload.upload_file",
              //     args: {
              //         file_url: img.value,
              //         folder_name: frm.doc.name,
              //         type: "POST",
              //     }, callback: () => {

              //     }
              // }))

              frappe.msgprint({
                title: __("Successful"),
                message: __(
                  "Upload Started, restarting app will restart unfinished uploads"
                ),
              });
            } catch (e) {
              nativeInterface.logToNative(e);
            }
          })
          .addClass("btn-primary");
        element.addClass("btn-primary");
        element.parent().removeClass("hidden-xs hidden-md");
      }
    });
  },
});
