frappe.pages['payment-redirect'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Payment Redirect',
		single_column: true
	});
	$(`<div class="dashboard" style="overflow-y: hidden">
	<div id="dashboard-graph" class="col-md-12">
	<div id="chart" class="col-md-12"></div>
	</div>`).appendTo($(wrapper).find(".page-content").empty());
	container = $(wrapper).find(".dashboard-graph");
	page = wrapper.page;
	get_student_data();
	// redirectToPayment();

}

function set_page(data) {

}


function get_student_data() {
	const queryString = window.location.search;
	const urlParams = new URLSearchParams(queryString);
	const payment_request = urlParams.get('payment_request');
	frappe.call({
		method: "edu_quality.fees.page.payment_redirect.get_payment_details",
		type: "GET",
		args: {
			doc: payment_request
		},
		callback: function (r) {
			console.log(r);
			var content = document.getElementById('chart');
			var html =
				`<div class="container mt-4 mb-4 p-3 d-flex justify-content-center">
    <div class="card p-4">
        <div class=" image d-flex flex-column justify-content-center align-items-center"> <button
                class="btn btn-secondary"> <img src="https://fees.walnutedu.in/bootstrap/images/walnut_icon.png" height="100"
                    width="100" /></button> <span class="name mt-3">` + r.message.student_name + `</span> <span
                class="idd">` + r.message.student_id + `</span>
            <div class="d-flex flex-row justify-content-center align-items-center gap-2"> 
				<span class="idd1"><b>Due Date:</b> </span>
				<span class="idd1">`+ r.message.due_date + `</span>
				</div>
            <div class="d-flex flex-row justify-content-center align-items-center mt-3"> 
				<span class="number">`+ r.message.due_amount + ` <span class="follow">INR</span></span> </div>
				<span class="number">Breakup</span>`
	var breakup = r.message.breakup
	breakup.forEach(element => {
		html = html + `<span class="follow">` + element.fees_category + " --- " + element.amount +`</span>`
	});
	html = html + `<div class=" d-flex mt-2"> <a href="`+ r.message.payment_url + `"><button class="btn1 btn-dark">Proceed To Pay</button></a> </div>
            <div class="text mt-3"> <span>Note : If the receipt is not generated, but the amount is deducted from your account then please send an email with transaction details to 'feedback@walnutedu.in'. </span> </div>
        	</div>
		</div>
	</div>
	<style>
	* {
		margin: 0;
		padding: 0
	}
	
	body {
		background-color: #000
	}
	
	.card {
		width: 350px;
		background-color: #efefef;
		border: none;
		cursor: pointer;
		transition: all 0.5s;
	}
	
	.image img {
		transition: all 0.5s
	}
	
	.card:hover .image img {
		transform: scale(1.5)
	}
	
	.btn {
		height: 140px;
		width: 140px;
		border-radius: 50%
	}
	
	.name {
		font-size: 22px;
		font-weight: bold
	}
	
	.idd {
		font-size: 14px;
		font-weight: 600
	}
	
	.idd1 {
		font-size: 12px
	}
	
	.number {
		font-size: 22px;
		font-weight: bold
	}
	
	.follow {
		font-size: 12px;
		font-weight: 500;
		color: #444444
	}
	
	.btn1 {
		height: 40px;
		width: 150px;
		border: none;
		background-color: #000;
		color: #aeaeae;
		font-size: 15px
	}
	
	.text span {
		font-size: 13px;
		color: #545454;
		font-weight: 500
	}
	
	.icons i {
		font-size: 19px
	}
	
	hr .new1 {
		border: 1px solid
	}
	
	.join {
		font-size: 14px;
		color: #a0a0a0;
		font-weight: bold
	}
	
	.date {
		background-color: #ccc
	}</style`;
	content.innerHTML = html;
		}

	})
}
function redirectToPayment() {
	const queryString = window.location.search;
	const urlParams = new URLSearchParams(queryString);
	const payment_request = urlParams.get('payment_request');
	frappe.call({
		method: "generate_payment_url",
		type: "GET",
		args: {
			doc: payment_request
		},
		callback: function (r) {
			window.location.replace(r.message);
		}

	})
}