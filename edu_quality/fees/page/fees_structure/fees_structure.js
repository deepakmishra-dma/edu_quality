frappe.pages['fees-structure'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Fee Structure',
		single_column: true
	});fee_type_form(wrapper);
}

async function fee_type_form(wrapper){
	$(`<div class="dashboard" style="overflow-y: hidden">
		<div class="dashboard-graph"></div>
		</div>`).appendTo($(wrapper).find(".page-content").empty());
	container = $(wrapper).find(".dashboard-graph");
	page = wrapper.page;
	form1 = `<table class="table1" style="margin:20px 20px 0;">
	<tbody><tr>
	<td><label  for="textinput">Financial Year : <span style="font-weight:bold; color:#F00;"> *</span></label></td>
	<td><label class="select">
	  <select id="ins_rel_head_type_academic_year" name="ins_rel_head_type_academic_year" style="width:300px" onchange="getinstallments();getFlags();getYearWiseData();">
		<option>Select Year</option>
		<option>2022-2023</option>
		<option>2023-2024</option>
		<option>2024-2025</option>
	  </select><i></i></label></td>
	</tr>
	<tr>
	  <td>
		<label>Class Name : <span style="font-weight:bold; color:#F00;">*</span></label>
	  </td>
	  <td>
		<label class="select">
		  <select id="class_name" name="class_name" class="validate[required]" onchange="getClassWiseData();" style="min-width: 80px;" autofocus="">
			<option value="">- Select Class -</option>
			 <option value="8">Playgroup</option>
			 <option value="9">Nursery</option>
			 <option value="10">Junior KG</option>
			 <option value="11">Senior KG</option>
			 <option value="12">1</option>
			 <option value="13">2</option>
			 <option value="14">3</option>
			 <option value="15">4</option>
			 <option value="16">5</option>
			 <option value="17">6</option>
			 <option value="18">7</option>
			 <option value="19">8</option>
			 <option value="20">Primary</option>
			 <option value="21">KG</option>
			 <option value="22">All</option>
			 <option value="23">9</option>
			 <option value="24">10</option>
			 <option value="25">11</option>
			 </select><i></i>
		</label>
	  </td>
	  <td style="display:none">
		<label>Installment : <span style="font-weight:bold; color:#F00;">*</span></label>
	  </td>
	  <td style="display:none">
		<label class="select">
		  <select id="installment_name1" name="installment_name1" class="validate[required]" onchange="getInstlInfo()" style="min-width: 200px;">
			  <option></option>
			 </select><i></i>
		</label>
	  </td>
	</tr>
	<tr>
	  <td style="display:none">Due Date : <span style="font-weight:bold; color:#F00;">**</span></td>
	  <td class="inline-group" style="display:none">
		<label class="radio">
		  <input type="radio" id="depoYes" name="isDepo" onchange="
			  this.form['instl_due_date'].disabled = false;
				 " checked="" value="1"><i></i>Yes </label>
		<label class="radio">
		  <input type="radio" id="depoNo" name="isDepo" onchange="
			  this.form['instl_due_date'].disabled = true;
				 " value="0"><i></i>No</label>
	  </td>
	  <td colspan="2" style="text-align: center;display:none">
		<div id="duedate" class="row">
		  <section class="col col-12">
			<label class="input">
			  <i class="icon-append fa fa-calendar"></i>
			  <input type="text" id="instl_due_date" name="instl_due_date" class="validate[required] field datepicker hasDatepicker" readonly="readonly">
			</label>
		  </section>
		</div>
	  </td>
	</tr>
	<!-- <tr style="display:none;">
	  <td colspan="4">** For Deposits Due Date not necessary.</td>
	</tr> -->
	<tr>
	  <td><input type="hidden" name="academic_year_selected" id="academic_year_selected"></td>
	</tr>
  	</tbody></table>`
	container.append(form1)
	form2 = `<table class="table1" style="margin:10px 10px 0;" id="dataTable" name="dataTable">
	<tbody><tr>
	  <td><input type="checkbox" name="chk"></td>
	  <td>
		<label>Fee Head Name : <span style="font-weight:bold; color:#F00;">*</span></label>
	  </td>
	  <td>
		<label class="select">
		  <select id="fee_head_name1" name="fee_head_name1[]" onchange="depo_chk()" class="validate[required]" style="min-width: 180px;">
		 </select><i></i>
		</label>
	  </td>
	  <td>
		<label>Amount : <span style="font-weight:bold; color:#F00;">*</span></label>
	  </td>
	  <td>
		<label class="input">
		  <i class="icon-append fa fa-rupee"></i>
		  <input type="text" id="fee_head_amt" name="fee_head_amt[]" class="validate[required,custom[onlyNumberSp]] " maxlength="11">
		</label>
	  </td>
	</tr>
	<tr>
	  <td></td>
	  </tr>
	  <tr id="new_data">
	  <td> </td>
	</tr>
  	</tbody></table>`
	container.append(form2)
	form3 = `<table class="table1" style="margin:5px 5px 0;">
	<tbody><tr>
	  <td>
							  <input value="Add Heads" onclick="addRow('dataTable')" class="button_new" type="button" title="Add More Fee Heads under this...">
						  </td>
	  <td>
							<input value="Remove Selected Heads" onclick="deleteRow('dataTable')" class="button_new" type="button" title="Remove selected Fee Heads from below...">
						  </td>
	</tr>
	<tr>
	  <td>Fee Refers To : <span style="font-weight:bold; color:#F00;">*</span></td>
	  <td class="inline-group">
		<label class="radio">
		  <input type="radio" id="yes" name="fee_refer" checked="" value="1"><i></i>Institute</label>
		<label class="radio">
		  <input type="radio" id="no" name="fee_refer" value="0"><i></i>School</label>
	  </td>
	  <td colspan="3">
		<div id="inst">
		  <label class="select">
			<select id="inst_name" name="inst_name[]" class="validate[required] " onchange="show_receipt_inst(this.value);" style="min-width: 190px;">
			  <option value="">- Select Institute -</option>
			   <option value="1">Unique Educational and Sports Foundation</option>
			   <option value="2">Rethink Educational Systems Pvt Ltd Shivane</option>
			   <option value="3">Rethink Educational Systems Pvt Ltd Fursungi</option>
			   <option value="4">Walnut School Shivane Registration Fees</option>
			   <option value="5">Baby Walnut Shivane</option>
			   <option value="6">Walnut School Fursungi Registration Fees</option>
			   <option value="7">Baby Walnut Fursungi</option>
			   <option value="8">Walnut School Shivane</option>
			   <option value="9">Walnut School Fursungi</option>
			   <option value="10">Walnut School Wakad</option>
			   <option value="11">Rethink Educational Systems Pvt Ltd Wakad</option>
			   <option value="12">Walnut School Wakad Registration Fees</option>
			   <option value="13">Baby Walnut Wakad</option>
			   </select><i></i>
		  </label>
		</div><div id="school" style="display: none;">
		  <label class="select">
			<select id="school_name" name="school_name[]" class="validate[required] " onchange="show_receipt_school(this.value);" style="min-width: 190px;">
			  <option value="">- Select School -</option>
			   <option value="2">Walnut School at Shivane</option>
			   </select><i></i>
		  </label>
		</div>
	  </td>
	  <td>
							  <input type="submit" style="" class="button_new" value="Save" name="add_relation" id="add_relation" onclick="return validateform()">
						  </td>
	  <td>
		<label>Last Receipt No. : </label>
	  </td>
	  <td><span id="last_receipt"></span></td>
	</tr>
  	</tbody></table>`
	container.append(form3)
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
			<th>Class Name</th>
			<th>Fee Head Name</th>
			<th>Fee Head Type</th>
			<th>Fee Head Amount</th>
			<th>Institute/School Name</th>
			<th>Financial Year</th>
			<th style="">Del</th>
		  </tr>
		  <tr>
		  <tr><td>Playgroup </td><td>Tuition Fee</td><td>Fee</td><td>0</td><td>Walnut School at Shivane</td><td>2023-2024</td><td style=""><a href="feesetup/removeFeeHeads.php?tab=tab4&amp;id=693"><img width="18" height="18" src="/files/remove.png" title="Remove this"></a></td></tr>`
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