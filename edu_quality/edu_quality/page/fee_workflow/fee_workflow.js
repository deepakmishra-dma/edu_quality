frappe.pages["fee-workflow"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Fee Workflow",
    single_column: true,
  });
  if (!window.Formio) {
    var script = document.createElement("script");
    script.onload = () => {
      window.Formio.setBaseUrl(window.location.origin);
      this.page.main = $(`
				<div id="quotation-wizard" class="p-4 layout-main-section frappe-card">
					<div id="formio"></div>
				</div>`).appendTo(this.page.main);
      Formio.createForm(document.getElementById("formio"), formJson, {
        hooks: {
          beforeNext(currentPage, submission, next) {
            if (currentPage.path === "page1") {
              next();
            }
          },
          beforeSubmit(submission, next) {
            frappe
              .call({
                method:
                  "edu_quality.edu_quality.page.fee_workflow.fee_workflow.create_fee_workflow",
                args: submission,
              })
              .then((r) => {
                frappe.set_route(`/app/fees`);
                location.reload();
              });
          },
        },
      }).then(function (form) {});
    };
    script.src =
      "/assets/edu_quality/node_modules/formiojs/dist/formio.full.js";
    document.head.appendChild(script); //or something of the likes
  }
  frappe.require(
    ["/assets/edu_quality/node_modules/formiojs/dist/formio.full.css"],
    () => {}
  );

  // frappe.call({
  // 	method: '/api/method/edu_quality.public.py.fee_structure.get_fee_structures',
  // 	args: {
  // 		'school': 'school',
  // 		'institution' : 'institution'
  // 	},
  // 	callback: function(r) {
  // 		console.log(r)
  // 		this.page.main = $(`<h1>Hello</h1>`).appendTo(this.page.main);
  // 	}
  // });

  container = $(wrapper);
  imp = document.createElement("table");
  imp.id = "table";
  imp.className = "table bg-white";
  imp.innerHTML =
    "<tr> <th>Class Name</th> <th>Fee Head Name</th> <th>Fee Head Type</th> <th>Fee Head Account</th> <th>Fee Head Institution/School</th> <th>Financial Year</th> </tr> <tr> <td>Class 1</td> <td>Tuition Fee</td> <td>Fee</td> <td>10000</td> <td>Walnut School</td> <td>2023-2024</td> </tr> <tr> <td>Class 1</td> <td>Tuition Fee</td> <td>Fee</td> <td>10000</td> <td>Walnut School</td> <td>2023-2024</td> </tr> <tr> <td>Class 1</td> <td>Tuition Fee</td> <td>Fee</td> <td>10000</td> <td>Walnut School</td> <td>2023-2024</td> </tr>";
  wrapper = document.createElement("div");
  wrapper.className = "text-center m-5";
  console.log(imp);
  wrapper.appendChild(imp);
  container.append(wrapper);
};

const formJson = {
  display: "wizard",
  settings: {
    pdf: {
      id: "1ec0f8ee-6685-5d98-a847-26f67b67d6f0",
      src: "https://files.form.io/pdf/5692b91fd1028f01000407e3/file/1ec0f8ee-6685-5d98-a847-26f67b67d6f0",
    },
  },
  components: [
    {
      title: "Fee structure",
      breadcrumb: "condensed",
      breadcrumbClickable: true,
      buttonSettings: {
        previous: false,
        cancel: false,
        next: true,
      },
      navigateOnEnter: false,
      saveOnEnter: false,
      scrollToTop: false,
      collapsible: false,
      key: "page1",
      type: "panel",
      label: "Specify Origin and Destination",
      input: false,
      tableView: false,
      components: [
        {
          label: "Columns",
          columns: [
            {
              components: [
                {
                  label: "Program",
                  widget: "choicesjs",
                  tableView: true,
                  dataSrc: "url",
                  data: {
                    url: "/api/resource/Program?limit=10000",
                    headers: [
                      {
                        key: "",
                        value: "",
                      },
                    ],
                  },
                  valueProperty: "name",
                  template: "<span>{{ item.name }}</span>",
                  validate: {
                    required: true,
                  },
                  key: "program",
                  type: "select",
                  lazyLoad: false,
                  selectValues: "data",
                  disableLimit: false,
                  noRefreshOnScroll: false,
                  input: true,
                },
                {
                  label: "Student Category",
                  widget: "choicesjs",
                  key: "studentCategory",
                  tableView: true,
                  dataSrc: "url",
                  data: {
                    url: "/api/resource/Student Category?limit=10000",
                    headers: [
                      {
                        key: "",
                        value: "",
                      },
                    ],
                  },
                  valueProperty: "name",
                  template: "<span>{{ item.name }}</span>",
                  selectValues: "data",
                  type: "select",
                  lazyLoad: false,
                  disableLimit: false,
                  noRefreshOnScroll: false,
                  input: true,
                },
                {
                  label: "School",
                  widget: "choicesjs",
                  key: "school",
                  tableView: true,
                  dataSrc: "url",
                  data: {
                    url: "/api/resource/School?limit=10000",
                    headers: [
                      {
                        key: "",
                        value: "",
                      },
                    ],
                  },
                  valueProperty: "name",
                  template: "<span>{{ item.name }}</span>",
                  selectValues: "data",
                  type: "select",
                  lazyLoad: false,
                  disableLimit: false,
                  noRefreshOnScroll: false,
                  input: true,
                },
              ],
              width: 6,
              offset: 0,
              push: 0,
              pull: 0,
              size: "md",
              currentWidth: 6,
            },
            {
              components: [
                {
                  label: "Academic Year",
                  widget: "choicesjs",
                  tableView: true,
                  dataSrc: "url",
                  data: {
                    url: "/api/resource/Academic Year?limit=10000",
                    headers: [
                      {
                        key: "",
                        value: "",
                      },
                    ],
                  },
                  valueProperty: "name",
                  template: "<span>{{ item.name }}</span>",
                  validate: {
                    required: true,
                  },
                  key: "academicYear",
                  type: "select",
                  lazyLoad: false,
                  selectValues: "data",
                  disableLimit: false,
                  noRefreshOnScroll: false,
                  input: true,
                },
                {
                  label: "Academic Term",
                  widget: "choicesjs",
                  key: "academicTerm",
                  tableView: true,
                  dataSrc: "url",
                  data: {
                    url: "/api/resource/Academic Term",
                    headers: [
                      {
                        key: "",
                        value: "",
                      },
                    ],
                  },
                  searchField: "query",
                  filter: (filters = [
                    ["'academic_year','='','{{row.academicYear}}'"],
                  ]),
                  valueProperty: "name",
                  template: "<span>{{ item.name }}</span>",
                  selectValues: "data",
                  type: "select",
                  disableLimit: true,
                  noRefreshOnScroll: false,
                  input: true,
                },
                {
                  label: "Institution",
                  widget: "choicesjs",
                  key: "institution",
                  tableView: true,
                  dataSrc: "url",
                  data: {
                    url: "/api/resource/Institution?limit=10000",
                    headers: [
                      {
                        key: "",
                        value: "",
                      },
                    ],
                  },
                  valueProperty: "name",
                  template: "<span>{{ item.name }}</span>",
                  selectValues: "data",
                  type: "select",
                  lazyLoad: false,
                  disableLimit: false,
                  noRefreshOnScroll: false,
                  input: true,
                },
              ],
              width: 6,
              offset: 0,
              push: 0,
              pull: 0,
              size: "md",
              currentWidth: 6,
            },
          ],
          key: "columns",
          type: "columns",
          input: false,
          tableView: false,
        },
        {
          label: "Components",
          tableView: false,
          rowDrafts: false,
          key: "editGrid",
          type: "editgrid",
          displayAsTable: false,
          input: true,
          components: [
            {
              label: "Columns",
              columns: [
                {
                  components: [
                    {
                      label: "Fees Category",
                      widget: "choicesjs",
                      tableView: true,
                      dataSrc: "url",
                      data: {
                        url: "/api/resource/Fee Category?limit=10000",
                        headers: [
                          {
                            key: "",
                            value: "",
                          },
                        ],
                      },
                      valueProperty: "name",
                      template: "<span>{{ item.name }}</span>",
                      validate: {
                        required: true,
                      },
                      key: "feesCategory",
                      type: "select",
                      lazyLoad: false,
                      selectValues: "data",
                      disableLimit: false,
                      noRefreshOnScroll: false,
                      input: true,
                    },
                  ],
                  offset: 0,
                  push: 0,
                  pull: 0,
                  size: "md",
                  currentWidth: 3,
                  width: 3,
                },
                {
                  components: [
                    {
                      label: "Amount",
                      applyMaskOn: "change",
                      mask: false,
                      tableView: false,
                      currency: "USD",
                      inputFormat: "plain",
                      truncateMultipleSpaces: false,
                      validate: {
                        required: true,
                      },
                      key: "amount",
                      type: "currency",
                      input: true,
                      delimiter: true,
                    },
                  ],
                  offset: 0,
                  push: 0,
                  pull: 0,
                  size: "md",
                  currentWidth: 3,
                  width: 3,
                },
                {
                  components: [
                    {
                      label: "Description",
                      applyMaskOn: "change",
                      autoExpand: false,
                      tableView: true,
                      key: "description",
                      type: "textarea",
                      input: true,
                    },
                  ],
                  size: "md",
                  offset: 0,
                  push: 0,
                  pull: 0,
                  width: 3,
                  currentWidth: 3,
                },
                {
                  components: [
                    {
                      label: "Fee Type",
                      widget: "choicesjs",
                      tableView: true,
                      dataSrc: "url",
                      data: {
                        url: "/api/resource/Fee Type?limit=10000",
                        headers: [
                          {
                            key: "",
                            value: "",
                          },
                        ],
                      },
                      valueProperty: "name",
                      template: "<span>{{ item.name }}</span>",
                      key: "feeType",
                      type: "select",
                      lazyLoad: false,
                      disableLimit: false,
                      noRefreshOnScroll: false,
                      input: true,
                      selectValues: "data",
                    },
                  ],
                  size: "md",
                  offset: 0,
                  push: 0,
                  pull: 0,
                  width: 3,
                  currentWidth: 3,
                },
              ],
              key: "columns",
              type: "columns",
              input: false,
              tableView: false,
            },
          ],
        },
      ],
    },
    {
      title: "Fee schedule",
      breadcrumb: "condensed",
      breadcrumbClickable: false,
      buttonSettings: {
        previous: false,
        cancel: false,
        next: true,
      },
      navigateOnEnter: false,
      saveOnEnter: false,
      scrollToTop: false,
      collapsible: false,
      key: "page2",
      type: "panel",
      label: "Schedule",
      input: false,
      tableView: false,
      allowPrevious: true,
      components: [
        {
          label: "Columns",
          columns: [
            {
              components: [
                {
                  label: "Due Date",
                  hideInputLabels: false,
                  inputsLabelPosition: "top",
                  useLocaleSettings: false,
                  tableView: false,
                  fields: {
                    day: {
                      hide: false,
                      required: true,
                    },
                    month: {
                      hide: false,
                      required: true,
                    },
                    year: {
                      hide: false,
                      required: true,
                    },
                  },
                  dayFirst: true,
                  defaultValue: "00/00/0000",
                  key: "dueDate",
                  type: "day",
                  input: true,
                },
              ],
              width: 6,
              offset: 0,
              push: 0,
              pull: 0,
              size: "md",
              currentWidth: 6,
            },
            {
              components: [
                {
                  label: " Send Payment Request Email",
                  tableView: false,
                  key: "sendPaymentRequestEmail",
                  type: "checkbox",
                  input: true,
                  defaultValue: false,
                },
              ],
              width: 6,
              offset: 0,
              push: 0,
              pull: 0,
              size: "md",
              currentWidth: 6,
            },
          ],
          key: "columns1",
          type: "columns",
          input: false,
          tableView: false,
        },
        {
          label: " Student Group",
          tableView: false,
          rowDrafts: false,
          key: "studentGroup",
          type: "editgrid",
          displayAsTable: false,
          input: true,
          components: [
            {
              label: "Columns",
              columns: [
                {
                  components: [
                    {
                      label: "Student Group",
                      widget: "choicesjs",
                      tableView: true,
                      dataSrc: "url",
                      data: {
                        url: "/api/resource/Student Group?limit=10000",
                        headers: [
                          {
                            key: "",
                            value: "",
                          },
                        ],
                      },
                      valueProperty: "name",
                      template: "<span>{{ item.name }}</span>",
                      validate: {
                        required: true,
                      },
                      searchField: "query",
                      filter: (filters = [
                        ["'program','='','{{row.program}}'"],
                      ]),
                      key: "studentGroup",
                      type: "select",
                      lazyLoad: true,
                      selectValues: "data",
                      disableLimit: false,
                      noRefreshOnScroll: false,
                      input: true,
                    },
                  ],
                  width: 6,
                  offset: 0,
                  push: 0,
                  pull: 0,
                  size: "md",
                  currentWidth: 6,
                },
                {
                  components: [
                    {
                      label: "Total Students",
                      applyMaskOn: "change",
                      mask: false,
                      tableView: false,
                      delimiter: false,
                      requireDecimal: false,
                      inputFormat: "plain",
                      truncateMultipleSpaces: false,
                      key: "totalStudents",
                      type: "number",
                      input: true,
                    },
                  ],
                  width: 6,
                  offset: 0,
                  push: 0,
                  pull: 0,
                  size: "md",
                  currentWidth: 6,
                },
              ],
              key: "columns",
              type: "columns",
              input: false,
              tableView: false,
            },
          ],
        },
      ],
    },
    {
      type: "button",
      label: "Submit",
      key: "submit",
      disableOnInvalid: true,
      input: true,
      tableView: false,
    },
  ],
};
