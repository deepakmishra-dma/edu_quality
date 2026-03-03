let FormInstance = null;
frappe.pages['petty-cash-tool'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Petty Cash Tool',
		single_column: true
	});

	window.Formio.setBaseUrl(window.location.origin);

	const mainSection = `
		<div class="p-4 layout-main-section frappe-card" style="width: 65%; margin: 0 auto;">
			<div id="formio"></div>
		</div>`;
	page.main = $(mainSection).appendTo(page.main);

	Formio.createForm(document.getElementById('formio'), formJson, {}).then(async (form) => {
		FormInstance = form;
		form.on('submit', (submission) => {
			handleFormSubmit(form, submission);
		});

		form.on('change', (event) => {
			handleOnChange(event)
		});
	});
}

const handleFormSubmit = (form, submission) => {
	frappe.call({
		method: 'edu_quality.edu_quality.page.petty_cash_tool.petty_cash_tool.petty_cash_submit',
		args: {
			data: submission.data
		},
		callback: (r) => {
			frappe.msgprint({
				message: __('Petty Cash Submitted Successfully'),
				title: __('Petty Cash Submitted'),
				indicator: 'green',
				primary_action: {
					label: __('Close'),
					action: function () {
						frappe.msg_dialog.hide();
					}
				}
			});

			// reset the form after submission
			resetForm(form);
		}
	});
};

const resetForm = (form) => {
	form.submission = {};
};


function updateField(key, value) {
	try {
		FormInstance.getComponent(key).setValue(value);
	} catch (error) {
		console.error("Error updating field:", error);
	}
}

function updateFieldProperties(key, property, value) {
	try {
		const element = FormInstance.getComponent(key);
		element.component[property] = value;
		element.redraw();
	} catch (error) {
		console.error("Error updating field properties:", error);
	}
}

async function handleSchoolChange(event, value) {
	const companyValue = event?.data?.company?.name;
	const typeValue = event?.data?.type;

	// Early return if the selected school doesn't have a name
	if (!value?.name) {
		updateField('company', '');
		return;
	}

	// Fetch the institution associated with the selected school
	const { message: schoolInstitution } = await frappe.db.get_value('School', value.name, 'institution');

	// Update the company field if it doesn't match the selected school's institution
	if (!companyValue || schoolInstitution?.institution !== companyValue) {
		if (!schoolInstitution?.institution) {
			updateField('company', '');
			return;
		}
		updateField('company', { name: schoolInstitution.institution });
	}

	if (typeValue === 'payment') {
		return
	} else if (typeValue === 'cashWithdrawal') {
		// Fetch the petty cash account for the selected school
		const { message: school } = await frappe.db.get_value('School', value.name, 'petty_cash_account');

		// Update the accountHead field based on the school's petty cash account or fallback to the company's default petty cash
		if (school.petty_cash_account) {
			updateField('accountHead', { name: school.petty_cash_account });
		} else if (companyValue) {
			const { message: company } = await frappe.db.get_value('Company', companyValue, 'default_petty_cash');
			if (company?.default_petty_cash) {
				updateField('accountHead', { name: company.default_petty_cash });
			}
		}

		// Disable the accountHead field if it has been set
		updateFieldProperties('accountHead', 'disabled', true);
	}
}


const getAccountAmount = async (company, account) => {
	const balance = await frappe.call({
		method: 'erpnext.accounts.utils.get_account_balances',
		args: {
			accounts: [{ value: account, account_currency: "INR" }],
			company: company,
		},
	});

	const [amount] = balance.message;
	return amount.balance || '';
}

async function handleTypeChange(event, value) {
	const companyValue = event?.data?.company?.name;
	const schoolValue = event?.data?.school?.name;

	if (!companyValue && !schoolValue) return;

	let accountHead = '';

	// Define a helper function to get the account value
	async function getAccount(doctype, name, field) {
		const { message } = await frappe.db.get_value(doctype, name, field);
		return message[field];
	}

	if (value === 'cashWithdrawal') {
		if (schoolValue) {
			accountHead = await getAccount('School', schoolValue, 'petty_cash_account');
		}
		if (companyValue && !accountHead) {
			accountHead = await getAccount('Company', companyValue, 'default_petty_cash');
		}
	} else if (value === 'payment') {
		updateField('accountHead', '');
		updateFieldProperties('accountHead', 'disabled', false);
		return;
	}

	if (accountHead) {
		accountHead = { name: accountHead };
	}

	updateField('accountHead', accountHead);
	// Make accountHead field disabled if accountHead is set and type is cashWithdrawal
	updateFieldProperties('accountHead', 'disabled', !!accountHead);
}


async function handleCompanyChange(event, value) {
	const { school } = event?.data || {};
	const schoolElement = FormInstance.getComponent('school');

	if (!value.name) {
		['accountHead', 'school', 'type'].forEach(field => updateField(field, ''));
		schoolElement.component.data.url = `/api/resource/School`;
		schoolElement.redraw();
		return;
	}

	if (!school?.name) {
		schoolElement.component.data.url = `/api/resource/School?filters=[[\"institution\",\"=\",\"${value.name}\"]]`;
		schoolElement.redraw();
	}
}


const handleOnChange = async (event) => {
	const key = event?.changed?.component?.key;
	const value = event?.changed?.value;

	if (key === 'school') {
		await handleSchoolChange(event, value);
	} else if (key == 'type') {
		await handleTypeChange(event, value);
	} else if (key == 'company') {
		await handleCompanyChange(event, value);
	}
};


formJson = {
	"display": "form",
	"settings": {
		"pdf": {
			"id": "1ec0f8ee-6685-5d98-a847-26f67b67d6f0",
			"src": "https://files.form.io/pdf/5692b91fd1028f01000407e3/file/1ec0f8ee-6685-5d98-a847-26f67b67d6f0"
		}
	},
	"components": [
		{
			"key": "fieldSet",
			"type": "fieldset",
			"label": "Field Set",
			"input": false,
			"tableView": false,
			"components": [
				{
					"label": "Columns",
					"columns": [
						{
							"components": [
								{
									"label": "Company",
									"widget": "choicesjs",
									"placeholder": "Choose Company",
									"tableView": true,
									"dataSrc": "url",
									"data": {
										"url": "/api/resource/Company",
										"headers": [
											{
												"key": "",
												"value": ""
											}
										]
									},
									"template": "<span>{{ item.name }}</span>",
									"validate": {
										"required": true
									},
									"validateWhenHidden": false,
									"key": "company",
									"type": "select",
									"selectValues": "data",
									"disableLimit": false,
									"noRefreshOnScroll": false,
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
									"label": "School",
									"widget": "choicesjs",
									"placeholder": "Choose School",
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
									"template": "<span>{{ item.name }}</span>",
									"validateWhenHidden": false,
									"key": "school",
									"type": "select",
									"selectValues": "data",
									"disableLimit": false,
									"noRefreshOnScroll": false,
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
					"key": "columns3",
					"type": "columns",
					"input": false,
					"tableView": false
				},
				{
					"label": "Columns",
					"columns": [
						{
							"components": [
								{
									"label": "Type",
									"widget": "choicesjs",
									"placeholder": "Choose Type",
									"tableView": true,
									"data": {
										"values": [
											{
												"label": "Payment",
												"value": "payment"
											},
											{
												"label": "Cash Withdrawal",
												"value": "cashWithdrawal"
											}
										]
									},
									"validate": {
										"required": true
									},
									"validateWhenHidden": false,
									"key": "type",
									"type": "select",
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
									"label": "Category",
									"widget": "choicesjs",
									"placeholder": "Choose Category",
									"tableView": true,
									"data": {
										"values": [
											{
												"label": "Primary",
												"value": "primary"
											},
											{
												"label": "KG",
												"value": "kg"
											}
										]
									},
									"validate": {
										"required": true
									},
									"validateWhenHidden": false,
									"key": "category",
									"type": "select",
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
					"key": "columns1",
					"type": "columns",
					"input": false,
					"tableView": false
				},
				{
					"label": "Account Head",
					"widget": "choicesjs",
					"placeholder": "Choose Account Head",
					"tableView": true,
					"dataSrc": "url",
					"data": {
						"url": "/api/resource/Account?filters=[[\"allow_in_petty_cash\", \"=\", \"1\"]]&limit=0",
						"headers": [
							{
								"key": "",
								"value": ""
							}
						]
					},
					"template": "<span>{{ item.name }}</span>",
					"validate": {
						"required": true
					},
					"validateWhenHidden": false,
					"key": "accountHead",
					"type": "select",
					"selectValues": "data",
					"disableLimit": false,
					"noRefreshOnScroll": false,
					"input": true
				},
				{
					"label": "Columns",
					"columns": [
						{
							"components": [
								{
									"label": "To/From",
									"placeholder": "Enter To/From",
									"applyMaskOn": "change",
									"tableView": true,
									"validate": {
										"required": true
									},
									"validateWhenHidden": false,
									"key": "to_from",
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
									"label": "Amount",
									"placeholder": "Enter Amount",
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
									"validateWhenHidden": false,
									"key": "amount",
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
				},
				{
					"label": "Columns",
					"columns": [
						{
							"components": [
								{
									"label": "Description",
									"placeholder": "Enter Description",
									"applyMaskOn": "change",
									"autoExpand": false,
									"tableView": true,
									"validateWhenHidden": false,
									"key": "description",
									"type": "textarea",
									"input": true,
									"rows": 2
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
									"label": "Upload",
									"tableView": false,
									"storage": "base64",
									"dir": "Petty Cash",
									"image": true,
									"uploadOnly": true,
									"webcam": false,
									"capture": false,
									"fileTypes": [
										{
											"label": "",
											"value": ""
										}
									],
									"validateWhenHidden": false,
									"key": "file",
									"type": "file",
									"imageSize": "300",
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
					"key": "columns2",
					"type": "columns",
					"input": false,
					"tableView": false
				}
			]
		},
		{
			"label": "Submit",
			"showValidations": false,
			"block": true,
			"disableOnInvalid": true,
			"tableView": false,
			"key": "submit",
			"type": "button",
			"input": true,
			"saveOnEnter": false
		}
	]
}