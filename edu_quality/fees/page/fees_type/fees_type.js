frappe.pages['fees-type'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Fee Type',
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
	<tbody>
	<tr>
	  <td><label  for="textinput">Financial Year : <span style="font-weight:bold; color:#F00;"> *</span></label></td>
	  <td><label class="select">
		<select id="head_type_academic_year" name="head_type_academic_year" style="width:300px">
		</select><i></i></label>
	  </td>
	</tr>
	<tr>
	  <td>
		<label>Fee Head Type : <span style="font-weight:bold; color:#F00;">*</span>
		</label>
	  </td>
	  <td width="300">
		<label class="input">
		  <input type="text" id="fee_head_type_name" name="fee_head_type_name" class="validate[required,custom[onlyLetterSp]] field" autofocus="">
		</label>
	  </td>
	</tr>
	<tr>
	  <td>
		<label>Fee Head Type Description : </label>
	  </td>
	  <td>
		<label class="textarea">
		  <textarea type="textarea" id="fee_head_type_dsc" name="fee_head_type_dsc" class="validate[required,custom[onlyLetterNumbercomma]]"></textarea>
		</label>
	  </td>
	</tr>
	<tr>
	  <td colspan="2" align="center">
							  <input type="submit" style="" class="button_new" value="Save" name="add_fee_type" id="add_fee_type" onclick="return submit_form()">
						  </td>
	</tr>
  </tbody></table> `
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
							<th>Head Type Name</th>
							<th>Head Type Description</th>
							<th>Financial Year</th>
							<th style="">Del</th>
						</tr>`
			res.forEach(ft =>{
				html = html + `<tr id="row-`+ ft.type + `"><td>`+ ft.type + "</td>"
				html = html +  "<td>"+ ft.description + "</td>"
				html = html +  "<td>"+ ft.financial_year + "</td>"
				html = html + `<td><img id='`+ ft.type + `' width="18" height="18" src="/files/remove.png" title="Remove this" onclick=delete_item(this.id)></td></tr>`
			})
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