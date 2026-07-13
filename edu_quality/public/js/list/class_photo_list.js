frappe.has_indicator = function (doctype) {
  if (doctype == "Class Photo") return false;
  // returns true if indicator is present
  if (frappe.model.is_submittable(doctype)) {
    return true;
  } else if (
    (frappe.listview_settings[doctype] || {}).get_indicator ||
    frappe.workflow.get_state_fieldname(doctype)
  ) {
    return true;
  } else if (
    frappe.meta.has_field(doctype, "enabled") ||
    frappe.meta.has_field(doctype, "disabled")
  ) {
    return true;
  } else if (
    frappe.meta.has_field(doctype, "status") &&
    frappe.get_meta(doctype).states.length
  ) {
    return true;
  }
  return false;
};

frappe.listview_settings["Class Photo"] = {
  onload: function (list_view) {
    list_view.get_meta_html = function (doc) {
      let html = "";

      let settings_button = null;

      // check if the button property is an array or object
      if (Array.isArray(this.settings.button)) {
        // we have more than one button

        settings_button = "";
        console.log(this.settings, this.settings.button, "aa");
        for (const button of this.settings.button) {
          // make sure you have a unique name for each button,
          // otherwise it won't work
          // TODO make sure each name is unique, now it only checks if name exists
          if (!button.name) {
            frappe.throw(
              "Button needs a unique 'name' when using multiple buttons."
            );
          }

          if (button && button.show(doc)) {
            settings_button += `
                              <span class="list-actions">
                                  <button class="btn btn-action btn-default btn-xs"
                                      data-name="${doc.name}" data-idx="${
              doc._idx
            }" data-action="${button.name}"
                                      title="${button.get_description(doc)}">
                                      ${button.get_label(doc)}
                                  </button>
                              </span>
                          `;
          }
        }
      }
      // business as usual
      html += `
                <div class="level-item list-row-activity hidden-xs">
                    <div class="hidden-md hidden-xs">
                        ${settings_button}
                    </div>

                </div>
    `;
      console.log(html);
      return html;
    };
    list_view.get_list_row_html = function (doc) {
      return this.get_list_row_html_skeleton(
        this.get_left_html(doc),
        this.get_right_html(doc),
        doc
      );
    };
    list_view.get_list_row_html_skeleton = function (
      left = "",
      right = "",
      details
    ) {
      // let assigned_users = JSON.parse(doc._assign || "[]");
      // if (assigned_users.length) {
      //     assigned_to = `<div class="custom-assignee-container list-assignments d-flex align-items-center">
      //           ${frappe.avatar_group(assigned_users, 3, { filterable: true })[0].outerHTML}
      //       </div>`;
      // }

      return `
                    <div class="list-row-container" tabindex="1">
                        <div class="level list-row">
                            <div class="level-left ellipsis">
                                ${left}
                            </div>
                            <div class="level-right text-muted ellipsis">

                            </div>
                        </div>
                        <div class="row-bottom-section d-flex justify-content-between align-items-center  bd-highlight" style="margin-left:40px; margin-bottom:16px; padding:8px 20px; border-radius:6px;  background:#F9F9F9;">
                          <div class="d-flex align-items-center">





                          </div>

                          <div class="level-right text-muted ellipsis">
                        <a href="/app/file/view/home/${details.name}">View Files</a>


                          </div>
                        </div>
                    </div>
                `;
    };
  },
  button: [
    {
      name: "btn-make-call",
      show: function (doc) {
        return true;
        // return window.isApp && doc.mobile_no;
      },
      get_label: function () {
        return __("Make a Call");
      },
      get_description: function (doc) {
        return "Call {0}", [doc.mobile_no];
      },
      action: function (doc) {
        const number = "+91" + doc.mobile_no;
        window.nativeInterface.execute("dialCall", { tel: number });
      },
    },
    {
      name: "btn-make-whatsapp",
      show: function (doc) {
        // return true
        return window.isApp && doc.mobile_no;
      },
      get_label: function () {
        return __("Whatsapp");
      },
      get_description: function (doc) {
        return "Call {0}", [doc.mobile_no];
      },
      action: function (doc) {
        window.nativeInterface.execute("openWhatsApp", {
          payloadNumber: doc.mobile_no,
          payloadText: "Hey",
        });
      },
    },
  ],

  // refresh: function () {
  //     const favContainer = document.querySelector(
  //         "#page-List\\/Lead\\/List > div.container.page-body > div.page-wrapper > div > div.row.layout-main > div.col.layout-main-section-wrapper > div.layout-main-section.frappe-card > div.frappe-list > div.result > header > div.level-left.list-header-subject > div.list-row-col.ellipsis.list-subject.level > span.level-item.list-liked-by-me.hidden-xs"
  //     );
  //     if (favContainer) favContainer.remove();

  //     const AssigneeContaiiner = document.querySelectorAll(
  //         ".custom-assignee-container .avatar.avatar-small"
  //     );
  //     if (AssigneeContaiiner.length > 0) {
  //         AssigneeContaiiner.forEach((assignee) => {
  //             assignee.style.width = "23px";
  //             assignee.style.height = "23px";
  //         });
  //     }

  //     const firstColumElements = document.querySelectorAll(".list-subject");
  //     if (firstColumElements.length > 0) {
  //         firstColumElements.forEach((col) => (col.style.flex = "1.35"));
  //     }

  //     const bottomContainers = document.querySelectorAll(".row-bottom-section");
  //     if (window.innerWidth <= 600 && bottomContainers.length > 0) {
  //         bottomContainers.forEach((container) => {
  //             container.style.marginLeft = "5px";
  //             container.style.padding = "6px 8px";
  //         });
  //     }
  // },
};
