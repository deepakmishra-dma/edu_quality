async function folderExists(parent, newFolder) {
  const formData = new FormData();
  formData.append("file_name", newFolder);
  formData.append("folder", parent);

  try {
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
  } catch (e) {}
}
function uploadImage(image, folder, image_name, docname) {
  return fetch(image)
    .then((res) => res.blob())
    .then((blob) => {
      const formData = new FormData();
      const file = new File([blob], "image.jpg");

      formData.append("file", file, image_name);
      formData.append("folder", "home/" + folder);
      formData.append("is_private", 1);
      formData.append("doctype", "Student ID Card");
      formData.append("docname", docname);

      formData.append(
        "method",
        "edu_quality.edu_quality.doctype.student_id_card.student_id_card.auto_crop"
      );
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

const checkIfRefNoExists = async (academicYear, school, refNo) => {
  try {
    const studentResponse = await frappe.db.get_list("Student", {
      filters: { reference_number: refNo, school },
      fields: ["name"],
    });

    const student = studentResponse?.[0];

    if (!student) throw new Error("Student doesn't exist");
    const enrollmentRes = await fetch(
      `/api/resource/Program Enrollment?fields=["name","custom_id_card"]&filters=[["student","like","${student.name}"],["academic_year","=","${academicYear}"]]`
    );
    const programEnrollment = (await enrollmentRes.json())?.data?.[0];
    if (!programEnrollment) throw new Error("Enrollment doesn't exist");

    const data = await fetch(
      `/api/resource/Student ID Card/${programEnrollment.custom_id_card}`
    );
    const idCardData = await data.json();
    if (!idCardData) throw new Error("ID Card doesn't exist");
    return idCardData.data;
  } catch (e) {
    frappe.msgprint(e.message);
  }
};

const updateIDCard = async (idCard, body) => {
  let res = await fetch(`/api/resource/Student ID Card/${idCard}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
  let data = res.json();
  return data.data;
};

frappe.listview_settings["Student ID Card"] = {
  refresh: function (listview) {
    listview.page.add_inner_button("ID Card Scanner", function () {
      let image = "";
      let d = new frappe.ui.Dialog({
        title: "Take ID Card Photo",
        fields: [
          {
            label: "School",
            fieldname: "school",
            fieldtype: "Link",
            options: "School",
            reqd: true,
          },
          {
            label: "Academic Year",
            fieldname: "academic_year",
            fieldtype: "Link",
            options: "Academic Year",
            reqd: true,
          },
          {
            label: "Scanner",
            fieldname: "scanbtn",
            fieldtype: "Button",
            click: async () => {
              const images = await nativeInterface.execute(
                "openWebViewScanner"
              );

              const [academicYear, school, refNo] = images?.data.split("/");
              // frappe.msgprint(academicYear, school, refNo)
              d.set_value("refNo", refNo);
              d.set_value("academic_year", academicYear);
              d.set_value("school", school);
            },
          },
          {
            label: "Enter Ref No",
            fieldname: "refNo",
            fieldtype: "Data",
            reqd: true,
          },
          {
            label: "Reset",
            fieldname: "reset_btn",
            fieldtype: "Button",
            click: () => {
              reset(d);
            },
          },

          {
            label: "Check",
            fieldname: "check_btn",
            fieldtype: "Button",
            click: async function () {
              academicYear = d["fields_dict"]["academic_year"]["input"].value;
              school = d["fields_dict"]["school"]["input"].value;
              refNo = d["fields_dict"]["refNo"]["input"].value;
              const idCard = await checkIfRefNoExists(
                academicYear,
                school,
                refNo
              );

              if (idCard) {
                image = idCard.photo_taken;
                d.set_value("earlier_timestamp", idCard.photo_taken_time);
                d.set_value("earlier_photo_id", idCard.id_card_given_on);
                d.set_value("earlier_status", idCard.status);
                d.set_value(
                  "photo",
                  `<img src='${idCard.photo_taken}' style ='height:100px;width:100px;object-fit:contain;'></img>`
                );
              }
            },
          },
          {
            label: "Earlier Photo Taken On",
            fieldname: "earlier_timestamp",
            fieldtype: "Data",
            read_only: true,
          },
          {
            label: "Earlier Photo Status",
            fieldname: "earlier_status",
            fieldtype: "Data",
            read_only: true,
          },
          {
            label: "Earlier ID Given on",
            fieldname: "earlier_photo_id",
            fieldtype: "Date",
            read_only: true,
          },
          {
            label: "Take photo",
            fieldname: "take_photo",
            fieldtype: "Button",
            read_only: true,
            click: async () => {
              const images = await nativeInterface.execute(
                "openWebViewCamera",
                {
                  multiple: false,
                }
              );
              const [img] = images;
              image = "data:image/jpg;base64," + img.base64;
              d.set_value(
                "photo",
                `<img src = '${image}' style ='height:100px;width:100px;object-fit:contain;'></img>`
              );
            },
          },
          {
            options:
              "<img src = '/private/files/2.png' style ='height:100px;width:100px;object-fit:contain;'></img>",
            label: "",
            fieldname: "photo",
            fieldtype: "HTML",
            read_only: true,
          },
        ],
        size: "large",
        primary_action_label: "Upload",
        async primary_action(values) {
          try {
            const idCard = await checkIfRefNoExists(
              values.academic_year,
              values.school,
              values.refNo
            );
            // console.log(idCard, 'ss', image)
            // frappe.msgprint(image)
            findAndToggleFooterButton(d, true, "Pending");
            if (!image || !idCard)
              return frappe.msgprint("Take a photo or id card not found");
            if (image == idCard.photo_taken)
              return frappe.msgprint(
                "Error uploading, image uploaded has the same file url as the previous one"
              );
            await folderExists(
              "Home",
              `${values.school}-${values.academic_year}`
            );
            const img = await uploadImage(
              image,
              `${values.school}-${values.academic_year}`,
              `${values.refNo}-${idCard.name}.jpg`,
              idCard.name
            );
            image = "";
            const payload = {
              ...idCard,
              status: "CLICKED",
              photo_taken_time: getMysqlDate(new Date()),
            };
            const data = await updateIDCard(idCard.name, payload);
            // const service_account = await frappe.get_single("Google Service Account")

            // await frappe.call({
            //     method: "edu_quality.api.google_drive_upload.upload_file",
            //     args: {
            //         file_url: img,
            //         folder_name: service_account.get('id_card_folder'),
            //         method: "",
            //         type: "POST",
            //     }, callback: () => {

            //     }
            // })
          } catch (e) {
            findAndToggleFooterButton(d, false, "Upload");
          } finally {
            findAndToggleFooterButton(d, false, "Upload");
          }
        },
      });

      d.show();
    });
  },
};

function getMysqlDate(jsDatetime) {
  return jsDatetime.toISOString().slice(0, 19).replace("T", " ");
}

function findAndToggleFooterButton(d, toggle, label) {
  const btn = $(d.footer).find("button");
  btn.html(label);
  btn.prop("disabled", toggle);
}
function reset(d) {
  image =
    "<img src = '/private/files/2.png' style ='height:100px;width:100px;object-fit:contain;'></img>";
  d.set_value("refNo", "");

  d.set_value("earlier_timestamp", "");
  d.set_value("earlier_status", "");
  d.set_value("earlier_photo_id", "");
}
