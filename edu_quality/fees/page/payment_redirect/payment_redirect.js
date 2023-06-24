frappe.pages['payment-redirect'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Payment Redirect',
		single_column: true
	});

	redirectToPayment();

}

function redirectToPayment(){
	const queryString = window.location.search;
	const urlParams = new URLSearchParams(queryString);
	const payment_request = urlParams.get('payment_request');
	frappe.call({
		method: "generate_payment_url",
		type: "GET",
		args:{
			doc: payment_request
		},
		callback: function(r){
			window.location.replace(r.message);
		}

	})
}