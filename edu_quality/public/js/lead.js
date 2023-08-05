var error_msg = {
    "academic_year":"Academic Year is required before pushing to MGR",
    "center":"School is required before pushing to MGR",
    "first_name":"First name is required before pushing to MGR",
    "fathers_phone":"Father's phone number is required before pushing to MGR",
    "class":"Class is required before pushing to MGR",
    "fathers_email":"father's email id is required before pushing to MGR",
    "gender":"Gender is required before pushing to MGR",
    "date_of_birth":"Date of Birth is required before pushing to MGR",
}

frappe.ui.form.on("Lead", {
    refresh:function(frm){
        setTimeout(()=>{
            frm.remove_custom_button('Add to Prospect', 'Action')
            frm.remove_custom_button('Customer','Opportunity','Quotation','Prospect','Create');
            frm.add_custom_button(__("Push To MGR"), function() {
            var errorKey = Object.keys(error_msg).find(error=>frm.doc[error]=== null || frm.doc[error]===undefined || frm.doc[error] ==='' )
            if(errorKey){
                frappe.msgprint({
                    title: __('Error'),
                    message: __(error_msg[errorKey]),
                    indicator: 'red'
                });
                return 
            }
                frappe.call({
        method:"edu_quality.api.student_application.create_student_application",
        type: "POST",
        args: {name:frm.docname},
    });
            })
    },10)
    },
    validate:function(frm){
        
        if(!frm.doc.date_of_birth || frm.doc.date_of_birth.trim()==='') return

        var birthDate = new Date( frm.doc.date_of_birth)
        if(birthDate ==="Invalid Date") return
        var year = birthDate.getFullYear()
        var month = birthDate.getMonth()
        var day = birthDate.getDay()
 
        if(new Date(year+6,month,day)>new Date()){
            frappe.msgprint({
                title: __('Error'),
                message: __('Date of Birth must be of atleast 6 years old'),
                indicator: 'red'
            });
            frappe.validated = false;
        }
    },
     center: function(frm) {

           frm.set_query("class", function() {
           return {
                "filters": {
                    "custom_school": frm.doc.center
                    }
                };
            });
        }
    });
    

