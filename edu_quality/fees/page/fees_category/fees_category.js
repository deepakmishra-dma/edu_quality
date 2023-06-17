frappe.pages['fees-category'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Fee Category',
		single_column: true
	});
	fee_type_form(wrapper);
}

async function fee_type_form(wrapper){
	$(`<div class="dashboard" style="overflow-y: hidden">
		<div class="dashboard-graph"></div>
		</div>`).appendTo($(wrapper).find(".page-content").empty());
	container = $(wrapper).find(".dashboard-graph");
	page = wrapper.page;
	form = `<table class="table1" style="margin:20px 20px 0;">
	<tbody><tr>
	  <td><label for="textinput">Financial Year : <span style="font-weight:bold; color:#F00;"> *</span></label></td>
	  <td><label class="select">
		<select id="head_type_academic_year" name="head_type_academic_year" style="width:300px">
		  <option>Select Year</option>
		  <option>2023-2024</option>
		  <option>2024-2025</option>
		</select><i></i></label>
	  </td>
	</tr>
	<tr>
	  <td>
		<label>Fee Head Type : <span style="font-weight:bold; color:#F00;">*</span>
		</label>
	  </td>
	  <td width="200px">
		<label class="select">
		  <select id="fee_headtype_id" name="fee_headtype_id" class="validate[required] field" autofocus="">
			<option value="">Select Fee Head Type</option>
			 <option value="4">Fee</option>
			 <option value="5">CAUTION MONEY DEPOSI</option>
			 <option value="7">OTHER FEE</option>
			 <option value="8">Curriclum Material Fee</option>
			 <option value="15">Walnut School Registration Fees</option>
									</select><i></i>
		</label>
	  </td>
	  <td width="200px">&nbsp;</td>
	</tr>
	<tr>
	  <td>
		<label>Fee Flag : <span style="font-weight:bold; color:#F00;">*</span>
		</label>
	  </td>
	  <td width="200px">
		<label class="select">
		  <select id="head_flag" name="head_flag" class="validate[required] field">
			<option value="">Select Flag</option>
			<option value="FEES">FEES</option>
			<option value="DEPO">DEPOSIT</option>
			<option value="BUS">BUS FEE</option>
			<option value="OTHER">OTHER FEE</option>
			<option value="EXAM">EXAM FEE</option>
		  </select><i></i>
		</label>
	  </td>
	</tr>
	<!-- Frequency (Fee Head Type Frequency) -->
	<tr>
	  <td>
		<label>Frequency : <span style="font-weight:bold; color:#F00;">*</span>
		</label>
	  </td>
	  <td width="200px">
		<label class="select">
		  <select id="fee_head_frequency" name="fee_head_frequency" class="validate[required] field" onchange="set_emailId()">
			<option value="">Select Frequency</option>
			<option selected="" value="once">Once</option>
			<option value="variable">Variable</option>
		  </select><i></i>
		</label>
	  </td>
	</tr>
	<!-- Email Addresses -->
	<tr>  
	  <td>
		<label>Email Addresses : 
		</label>
	  </td>
	  <td width="200px">
		<label class="input">
		  <input type="text" id="fee_head_emails" name="fee_head_emails" placeholder="Enter comma separated emails" class="field">
		</label>
	  </td>
	</tr>

	<tr>
	  <td>
		<label>Fee Head Name : <span style="font-weight:bold; color:#F00;">*</span>
		</label>
	  </td>
	  <td colspan="2" width="400px">
		<label class="textarea">
		  <textarea type="text" id="fee_head_name" name="fee_head_name" class="validate[required] field" maxlength="128"></textarea>
		</label>
	  </td>
	</tr>

	<tr>
	  <td>
								<input type="submit" style="" class="button" value="Save" name="add_fee_head" id="add_fee_head" onclick="return validateform()">
						  </td>
	</tr>
  </tbody></table>`
	container.append(form)
	get_fin_yr()
	table = `
	<div style='height:50px'></div>
	<style>
	.table3 th{
		border: 1px solid black;
		padding: 4px 5px;
		border-collapse: collapse;
	  }
	.table3 th {
		padding: 4px 5px;
		text-align: left;
		background-color: #F8B259;
		color: #FFFFFF;
		opacity: 0.8;
	}
	.table3 td{
		padding: 4px 5px;
	}
	.table3, .table3 th, .table3 td {
		border: 1px solid #cce6ff;
		border-collapse: collapse;
	}
	</style>
	<table cellpadding="0" cellspacing="0" id='table3' class="table3" style="width:100%; margin:0 auto;">
	</table>`
	container.append(table)
	get_table()
}


function delete_item(item){
	frappe.call({
		method: 'delete_fee_type',
		type: "POST",
		args: {
			'fee_type': item
		},
	callback: function(r){
		row = document.getElementById("row-"+item).remove()
	}
})
}

async function get_table(){
	frappe.db.get_list('Fee Type',{fields:['type','description','financial_year']}).then(
		res =>{
			var table = document.getElementById('table3')
			table.innerHTML = ''
			var html = `<tbody><tr>
			<th>Head Name</th>
			<th>Head Flag</th>
			<th>Head Type</th>
			<th>Financial Year</th>
			<th style="">Del</th>
		  </tr>
		  <tr><td>Curriculum Material Fee</td><td>FEES</td><td>Fee</td><td>2023-2024</td><td style=""><a href="feesetup/removeFeeHeads.php?tab=tab2&amp;id=69"><img width="18" height="18" src="/files/remove.png" title="Remove this"></a></td></tr>`
			// res.forEach(ft =>{
			// 	html = html + `<tr id="row-`+ ft.type + `"><td>`+ ft.type + "</td>"
			// 	html = html +  "<td>"+ ft.description + "</td>"
			// 	html = html +  "<td>"+ ft.financial_year + "</td>"
			// 	html = html + `<td><img id='`+ ft.type + `' width="18" height="18" src="/files/remove.png" title="Remove this" onclick=delete_item(this.id)></td></tr>`
			// })
			html = html + '</tbody>'
			table.innerHTML = html
		}
	)
}

function get_fin_yr(){
	frappe.db.get_list('Financial Year').then(
		res =>{
			let select = document.getElementById('head_type_academic_year')
			res.forEach(yr =>{
				let option = document.createElement('option')
				option.value = yr.name
				option.innerHTML = yr.name
				select.appendChild(option)
			})
		}
	)
}

async function submit_form(){
	var fin_yr = document.getElementById('head_type_academic_year').value 
	if(fin_yr == 'Select Year'){
		frappe.throw('Please Select Financial Year!')
	}
	var fee_type = document.getElementById('fee_head_type_name').value 
	var description = document.getElementById('fee_head_type_dsc').value 
	if(fee_type == ''){
		frappe.throw('Please Enter a Fee Type!')
	}
	frappe.db.exists("Fee Type",fee_type).then(
		res => {if(res){
			frappe.throw('Fee Type Already Exists!')
		} }
	)
	frappe.call({
		method: 'insert_fee_type',
		type: "POST",
		args: {
			'fin_yr': fin_yr,
			'desc': description,
			'fee_type': fee_type
		},
	callback: function(r){
		get_table()
	}
})
}