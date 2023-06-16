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

function submit_form(){
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
		}
	})
	
}