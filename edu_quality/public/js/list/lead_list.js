frappe.listview_settings['Lead'] = {
  hide_name_column: true,
  button: {
    show(doc) {
      return doc.fathers_phone;
    },
    get_label() {
      return '<img src="https://static.vecteezy.com/system/resources/thumbnails/000/423/339/small/Multimedia__2850_29.jpg" width="14",height="14">';
    },
    get_description(doc) {
      return __('Copy {0}', [`${doc.fathers_phone}`])
    },
    action(doc) {
      var tempTextarea = document.createElement('textarea');
      tempTextarea.value = doc.fathers_phone;
      document.body.appendChild(tempTextarea);
      tempTextarea.select();
      document.execCommand('copy');
      document.body.removeChild(tempTextarea);
    }
  },
  onload: function (list_view) {
    list_view.page.add_action_item("Create a Broadcast Group", () => {
      const selectedLeads = list_view?.get_checked_items(true); console.log(selectedLeads)
      const broadCastDialog = new frappe.ui.Dialog({
        title: "Create a BroadCast Group",
        fields: [
          {
            fieldtype: "Link",
            label: "Name",
            options: "Broadcast Group",
            fieldname: "group_name",
            reqd: true,
          },
        ],
        size: "small",
        primary_action_label: "Join",

        primary_action: async function (values) {

          const payload = {

            "group_members": selectedLeads?.map((lead) => { return { member_name: lead } }) || []
          }
          try {
            const headers = new Headers()
            headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
            headers.append('content', 'application/json')
            const groupName = values.group_name
            const doc = await fetch(`/api/resource/Broadcast Group/${groupName}`, { headers: headers })
            const docData = await doc.json()
            payload.group_members = [...(docData.group_members || []), ...payload.group_members]
            const res = await fetch(`/api/resource/Broadcast Group/${groupName}`, {
              method: 'PUT',
              headers: headers, body: JSON.stringify(payload)
            })

            if (res.status === 200) {
              broadCastDialog.hide();
              const json = await res.json()

              frappe.msgprint({
                title: __('Success'),
                message: __('Broadcast Group Joined Successfully'),
                primary_action: {
                  action(values) {
                    frappe.set_route("app", "broadcast-group", groupName)
                  }
                }
              });
            }

          }

          catch (e) {

          }

        },
      });

      broadCastDialog.show();
    })



  }
}