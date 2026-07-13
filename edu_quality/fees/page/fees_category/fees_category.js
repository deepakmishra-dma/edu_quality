frappe.pages["fees-category"].on_page_load = function (wrapper) {
  var page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Fee Category",
    single_column: true,
  });
  fee_type_form(wrapper);
};

async function fee_type_form(wrapper) {
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
								<input type="submit" style="" class="button" value="Save" name="add_fee_head" id="add_fee_head" onclick="return submit_form()">
						  </td>
	</tr>
  </tbody></table>`;
  container.append(form);
  get_fin_yr();
  get_fee_type();
  get_fee_flag();
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
	</table>`;
  container.append(table);
  get_table();
}

function delete_item(item) {
  frappe.call({
    method: "delete_fee_category",
    type: "POST",
    args: {
      fee_category: item,
    },
    callback: function (r) {
      row = document.getElementById("row-" + item).remove();
    },
  });
}

async function get_table() {
  frappe.db
    .get_list("Fee Category", {
      fields: ["category_name", "fee_flag", "financial_year", "fee_type"],
    })
    .then((res) => {
      var table = document.getElementById("table3");
      table.innerHTML = "";
      var html = `<tbody><tr>
			<th>Head Name</th>
			<th>Head Flag</th>
			<th>Head Type</th>
			<th>Financial Year</th>
			<th style="">Del</th>
		  	</tr>`;
      res.forEach((fc) => {
        html =
          html +
          `<tr id="row-` +
          fc.category_name +
          `"><td>` +
          fc.category_name +
          "</td>";
        html = html + "<td>" + fc.fee_flag + "</td>";
        html = html + "<td>" + fc.fee_type + "</td>";
        html = html + "<td>" + fc.financial_year + "</td>";
        html =
          html +
          `<td><img id='` +
          fc.category_name +
          `' width="18" height="18" src="/files/remove.png" title="Remove this" onclick=delete_item(this.id)></td></tr>`;
      });
      html = html + "</tbody>";
      table.innerHTML = html;
    });
}

function get_fin_yr() {
  frappe.db.get_list("Financial Year").then((res) => {
    let select = document.getElementById("head_type_academic_year");
    res.forEach((yr) => {
      let option = document.createElement("option");
      option.value = yr.name;
      option.innerHTML = yr.name;
      select.appendChild(option);
    });
  });
}

function get_fee_type() {
  frappe.db.get_list("Fee Type").then((res) => {
    let select = document.getElementById("fee_headtype_id");
    res.forEach((ft) => {
      let option = document.createElement("option");
      option.value = ft.name;
      option.innerHTML = ft.name;
      select.appendChild(option);
    });
  });
}

function get_fee_flag() {
  frappe.db.get_list("Fee Flag").then((res) => {
    let select = document.getElementById("head_flag");
    res.forEach((fl) => {
      let option = document.createElement("option");
      option.value = fl.name;
      option.innerHTML = fl.name;
      select.appendChild(option);
    });
  });
}

async function submit_form() {
  var fin_yr = document.getElementById("head_type_academic_year").value;
  if (fin_yr == "") {
    frappe.throw("Please Select Financial Year!");
  }
  var ft = document.getElementById("fee_headtype_id").value;
  if (ft == "") {
    frappe.throw("Please Select Fee Head Type!");
  }
  var flag = document.getElementById("head_flag").value;
  if (flag == "") {
    frappe.throw("Please Select Flag!");
  }
  var fq = document.getElementById("fee_head_frequency").value;
  if (fq == "") {
    frappe.throw("Please Select Frequency!");
  }
  var email = document.getElementById("fee_head_emails").value;
  var fee_head = document.getElementById("fee_head_name").value;
  if (fee_head == "") {
    frappe.throw("Please Enter a FEE HEAD!");
  }
  frappe.db.exists("Fee Category", fee_head).then((res) => {
    if (res) {
      frappe.throw("Fee Category Already Exists!");
    }
  });
  frappe.call({
    method: "insert_fee_category",
    type: "POST",
    args: {
      fin_yr: fin_yr,
      fee_type: ft,
      flag: flag,
      fq: fq,
      email: email,
      fee_head: fee_head,
    },
    callback: function (r) {
      get_table();
    },
  });
}
