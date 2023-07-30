frappe.pages['payment-plan-creatio'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Payment Plan Creation Tool',
		single_column: true
	});
	if (!window.Formio) {
		var script = document.createElement('script');
		script.onload = () => {
			window.Formio.setBaseUrl(window.location.origin)
			this.page.main = $(`
				<div id="quotation-wizard" class="p-4 layout-main-section frappe-card">
					<div id="formio"></div>
				</div>`).appendTo(this.page.main);
			Formio.createForm(document.getElementById('formio'), formJson, {
				hooks: {
					
					beforeSubmit(submission, next) {
						if (!validateInvoicePortions(submission)) {
                            return
                        }
						else {
							frappe.call({
								method: 'edu_quality.edu_quality.page.payment_plan_creatio.payment_plan_creation.create_payment_plans',
								args: submission
							}).then(r => {
                                console.log("+++++++++++++1")
                                console.log(r)
                                if(r.message==true)
                                {
								frappe.set_route(`/app/payment-plan`)
								location.reload()
                                }
							})
						}
					}

				}
			}).then(function (form) {


			});
		};
		script.src = "/assets/edu_quality/node_modules/formiojs/dist/formio.full.js";
		document.head.appendChild(script); //or something of the likes

	}
	frappe.require(["/assets/edu_quality/node_modules/formiojs/dist/formio.full.css"], () => {

	})


}

function validateInvoicePortions(submission) {
    const classes = {}; // Object to store class-wise invoicePortion totals

    // Iterate through the form submissions to calculate invoicePortion totals for each class
    submission.data.paymentTerms.forEach(term => {
        const className = term.class;
        const invoicePortion = parseFloat(term.invoicePortion) || 0;

        if (!classes[className]) {
            classes[className] = 0;
        }

        classes[className] += invoicePortion;
    });

    // Check if any class has invoicePortion total exceeding 100
    for (const className in classes) {
        if (classes[className] !=100) {
            frappe.throw(`Total invoicePortion value for each class must not exceed 100.for ${className}`)
            // return false; // Validation failed
        }
    }

    return true; // Validation passed
}


const formJson = {
    "display": "form",
    "settings": {
        "pdf": {
            "id": "1ec0f8ee-6685-5d98-a847-26f67b67d6f0",
            "src": "https://files.form.io/pdf/5692b91fd1028f01000407e3/file/1ec0f8ee-6685-5d98-a847-26f67b67d6f0"
        }
    },
    "components": [
        {
            "label": "Columns",
            "columns": [
                {
                    "components": [
                        {
                            "label": "Plan Name",
                            "applyMaskOn": "change",
                            "tableView": true,
                            "validate": {
                                "required": true
                            },
                            "key": "planName",
                            "type": "textfield",
                            "input": true
                        }
                    ],
                    "width": 6,
                    "offset": 0,
                    "push": 0,
                    "pull": 0,
                    "size": "md",
                    "currentWidth": 6
                },
                {
                    "components": [
                        {
                            "label": "Academic Year",
                            "widget": "choicesjs",
                            "tableView": true,
                            "dataSrc": "url",
                            "data": {
                                "url": "/api/resource/Academic Year",
                                "headers": [
                                    {
                                        "key": "",
                                        "value": ""
                                    }
                                ]
                            },
                            "idPath": "name",
                            "valueProperty": "name",
                            "template": "<span>{{ item.name }}</span>",
                            "validate": {
                                "required": true
                            },
                            "key": "academicYear",
                            "type": "select",
                            "input": true,
                            "selectValues": "data",
                            "disableLimit": false,
							"lazyLoad": false,
                            "noRefreshOnScroll": false
                        }
                    ],
                    "width": 6,
                    "offset": 0,
                    "push": 0,
                    "pull": 0,
                    "size": "md",
                    "currentWidth": 6
                }
            ],
            "key": "columns",
            "type": "columns",
            "input": false,
            "tableView": false
        },
        {
            "label": "School",
            "widget": "choicesjs",
            "tableView": true,
            "dataSrc": "url",
            "data": {
                "url": "/api/resource/School",
                "headers": [
                    {
                        "key": "",
                        "value": ""
                    }
                ]
            },
            "idPath": "name",
            "valueProperty": "name",
            "template": "<span>{{ item.name }}</span>",
            "validate": {
                "required": true
            },
			"lazyLoad": false,
            "key": "school",
            "type": "select",
            "input": true,
            "selectValues": "data",
            "disableLimit": false,
            "noRefreshOnScroll": false
        },
        {
            "label": "Payment Terms",
            "tableView": false,
            "validate": {
                "required": true
            },
            "rowDrafts": false,
            "key": "paymentTerms",
            "type": "editgrid",
            "displayAsTable": false,
            "input": true,
            "components": [
                {
                    "label": "Columns",
                    "columns": [
                        {
                            "components": [
                                {
									"label": "Class",
									"widget": "choicesjs",
									"tableView": true,
									"dataSrc": "url",
									"data": {
										"url": `/api/resource/Program?filters=[["custom_school","=","{{data.school}}"]]`,
										"headers": [
											{
												"key": "",
												"value": ""
											}
										]
									},
									"valueProperty": "name",
									"template": "<span>{{ item.name }}</span>",
									"validate": {
										"required": true
									},
									"key": "class",
									"type": "select",
									"lazyLoad": true,
									"selectValues": "data",
									"disableLimit": true,
									"noRefreshOnScroll": false,
									"input": true
								},
                                {
                                    "label": "Due Date",
                                    "format": "yyyy-MM-dd",
                                    "tableView": false,
                                    "datePicker": {
                                        "disableWeekends": false,
                                        "disableWeekdays": false
                                    },
                                    "enableTime": false,
                                    "enableMinDateInput": false,
                                    "enableMaxDateInput": false,
                                    "key": "dueDate",
                                    "type": "datetime",
                                    "input": true,
                                    "validate": {
                                        "required": true
                                    },
                                    "widget": {
                                        "type": "calendar",
                                        "displayInTimezone": "viewer",
                                        "locale": "en",
                                        "useLocaleSettings": false,
                                        "allowInput": true,
                                        "mode": "single",
                                        "enableTime": false,
                                        "noCalendar": false,
                                        "format": "yyyy-MM-dd",
                                        "hourIncrement": 1,
                                        "minuteIncrement": 1,
                                        "time_24hr": false,
                                        "minDate": null,
                                        "disableWeekends": false,
                                        "disableWeekdays": false,
                                        "maxDate": null
                                    }
                                }
                            ],
                            "width": 6,
                            "offset": 0,
                            "push": 0,
                            "pull": 0,
                            "size": "md",
                            "currentWidth": 6
                        },
                        {
                            "components": [
                                {
                                    "label": "Payment Term",
                                    "widget": "choicesjs",
                                    "tableView": true,
                                    "dataSrc": "url",
                                    "data": {
                                        "url": "/api/resource/Payment Term",
                                        "headers": [
                                            {
                                                "key": "",
                                                "value": ""
                                            }
                                        ]
                                    },
                                    "idPath": "name",
                                    "valueProperty": "name",
									"template": "<span>{{ item.name }}</span>",
                                    "validate": {
                                        "required": true
                                    },
                                    "key": "paymentTerm",
                                    "type": "select",
                                    "input": true,
                                    "selectValues": "data",
                                    "disableLimit": false,
                                    "noRefreshOnScroll": false
                                },
                                {
                                    "label": "Invoice Portion",
                                    "applyMaskOn": "change",
                                    "mask": false,
                                    "tableView": false,
                                    "delimiter": false,
                                    "requireDecimal": false,
                                    "inputFormat": "plain",
                                    "truncateMultipleSpaces": false,
                                    "validate": {
                                        "required": true
                                    },
                                    "key": "invoicePortion",
                                    "type": "number",
                                    "input": true
                                }
                            ],
                            "width": 6,
                            "offset": 0,
                            "push": 0,
                            "pull": 0,
                            "size": "md",
                            "currentWidth": 6
                        }
                    ],
                    "key": "columns",
                    "type": "columns",
                    "input": false,
                    "tableView": false
                }
            ]
        },
        {
            "type": "button",
            "label": "Submit",
            "key": "submit",
            "disableOnInvalid": true,
            "input": true,
            "tableView": false
        }
    ]
}