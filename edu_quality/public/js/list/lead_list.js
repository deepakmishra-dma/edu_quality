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
    onload:function(lsit_view){
        list_view.add_action_item("Create a Broadcast Group",()=>{
            const selectedLeads =   list_view?.get_checked_items(true)
            const broadCastDialog = new frappe.ui.Dialog({
                title: "Create a BroadCast Group",
                fields: [
                  {
                    fieldtype: "Data",
                    label: "Name",
                    fieldname: "group_name",
                    reqd: true,
                  },
                ],
                size: "small",
                primary_action_label: "Create",
                primary_action(values) {
                    const payload = {
                    
                    }
                  selectedLeads.forEach((doc) => {
                    frappe.call({
                      method:
                        "nextai.funnel.doctype.funnel_task.triggers.on_custom_trigger.trigger",
                      args: {
                        trigger_name: values.funnel_name,
                        doctype: doctype,
                        doctype_name: doc,
                      },
                    });
                  });
                  d.hide();
                },
              });
    
              d.show();
        })
   
        
    
    }
}