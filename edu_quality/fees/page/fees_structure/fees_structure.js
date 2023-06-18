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
	  <select id="ins_rel_head_type_academic_year" name="ins_rel_head_type_academic_year" style="width:300px">
	  </select><i></i></label></td>
	</tr>
	<tr>
	  <td>
		<label>Class Name : <span style="font-weight:bold; color:#F00;">*</span></label>
	  </td>
	  <td>
		<label class="select">
		  <select id="class_name" name="class_name" class="validate[required]" onchange="getClassWiseData();" style="min-width: 80px;" autofocus="">
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
	  <td><input type="checkbox" name="chk" style="display:none"></td>
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
	<tbody><tr style="display:none;">
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
			<select id="inst_name" name="inst_name[]" class="validate[required]" style="min-width: 190px;">
			   </select><i></i>
		  </label>
		</div><div id="school" style="display: none;">
		  <label class="select">
			<select id="school_name" name="school_name[]" class="validate[required]" style="min-width: 190px;">
			   </select><i></i>
		  </label>
		</div>
	  </td>
	  <td>
							  <input type="submit" style="" class="button_new" value="Save" name="add_relation" id="add_relation" onclick="submit_form()">
						  </td>
	  <td>
		<label>Last Receipt No. : </label>
	  </td>
	  <td><span id="last_receipt"></span></td>
	</tr>
  	</tbody></table>`
	container.append(form3)
	get_fin_yr()
	get_class()
	get_fee_category()
	get_institution()
	get_school()
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
	const radioButtons = document.querySelectorAll('input[name="fee_refer"]');
	radioButtons.forEach(radio => {
		radio.addEventListener('click', handleRadioClick);
	});
}


function delete_item(item){
	frappe.call({
		method: 'delete_fee_structure',
		type: "POST",
		args: {
			'fee_structure': item
		},
	callback: function(r){
		row = document.getElementById("row-"+item).remove()
	}
})
}

async function get_table(){
	frappe.call({
		method: 'get_fee_structure',
		type: "GET",
	callback: function(r){
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
		<tr>`
		r.message.forEach(fs =>{
					html = html + `<tr id="row-`+ fs.name + `"><td>`+ fs.program + "</td>"
					html = html +  "<td>"+ fs.category + "</td>"
					html = html +  "<td>"+ fs.type + "</td>"
					html = html +  "<td>"+ fs.amount + "</td>"
					html = html +  "<td>"+ fs.school + "</td>"
					html = html +  "<td>"+ fs.fin_yr + "</td>"
					html = html + `<td><img id='`+ fs.name + `' width="18" height="18" src="/files/remove.png" title="Remove this" onclick=delete_item(this.id)></td></tr>`
				})
			html = html + '</tbody>'
			table.innerHTML = html
		}
	})
}

function get_fin_yr(){
	frappe.db.get_list('Financial Year').then(
		res =>{
			let select = document.getElementById('ins_rel_head_type_academic_year')
			res.forEach(yr =>{
				let option = document.createElement('option')
				option.value = yr.name
				option.innerHTML = yr.name
				select.appendChild(option)
			})
		}
	)
}

function get_class(){
	frappe.db.get_list('Program').then(
		res =>{
			let select = document.getElementById('class_name')
			res.forEach(yr =>{
				let option = document.createElement('option')
				option.value = yr.name
				option.innerHTML = yr.name
				select.appendChild(option)
			})
		}
	)
}
function get_school(){
	frappe.db.get_list('School').then(
		res =>{
			let select = document.getElementById('school_name')
			res.forEach(yr =>{
				let option = document.createElement('option')
				option.value = yr.name
				option.innerHTML = yr.name
				select.appendChild(option)
			})
		}
	)
}

function get_institution(){
	frappe.db.get_list('Institution').then(
		res =>{
			let select = document.getElementById('inst_name')
			res.forEach(yr =>{
				let option = document.createElement('option')
				option.value = yr.name
				option.innerHTML = yr.name
				select.appendChild(option)
			})
		}
	)
}

function get_fee_category(){
	frappe.db.get_list('Fee Category').then(
		res =>{
			let select = document.getElementById('fee_head_name1')
			res.forEach(ft =>{
				let option = document.createElement('option')
				option.value = ft.name
				option.innerHTML = ft.name
				select.appendChild(option)
			})
		}
	)
}

async function submit_form(){
	var fin_yr = document.getElementById('ins_rel_head_type_academic_year').value 
	if(fin_yr == 'Select Year'){
		frappe.throw('Please Select Financial Year!')
	}
	var class_name = document.getElementById('class_name').value 
	if(class_name==''){
		frappe.throw('Please Select the Class!')
	}
	var fee_type = document.getElementById('fee_head_name1').value  
	if(fee_type == ''){
		frappe.throw('Please Select a Fee Head!')
	}
	var amount = document.getElementById('fee_head_amt').value 
	if(amount == ''){
		frappe.throw('Please Enter an Amount!')
	}
	var institution = document.getElementById('yes').value 
	if(institution){
	var ins_name = document.getElementById('inst_name').value}
	else{
		var ins_name = document.getElementById('school_name').value
	}
	frappe.call({
		method: 'insert_fee_structure',
		type: "POST",
		args: {
			'fin_yr': fin_yr,
			'class_name': class_name,
			'fee_type': fee_type,
			'amount':amount,
			'is_ins':institution,
			'ins_name': ins_name
		},
	callback: function(r){
		get_table()
	}
})
}

function handleRadioClick() {
	ins = document.getElementById('inst')
	sch = document.getElementById('school')
	if (document.getElementById('yes').checked) {
	  ins.style.display = 'block';
	  sch.style.display = 'none';
	} else {
	  ins.style.display = 'none';
	  sch.style.display = 'block';
	}
  }

  
