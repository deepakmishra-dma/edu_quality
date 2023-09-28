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

var subStatuses = {
    'fresh':["Not Known","Online Enquiry","Telephonic Enquiry","Walkin Enquiry"],
    'warm':["Center Visit Planned","School Visit Done"],
    'followup/callback':["Call back later",
        "Call not answering",
        "Curious",
        "Interaction Done",
       "Not Reachable",
        "School Visit Done",
        "Switched Off",
        "Trial Class",],
        "hot":["Followup for Enrollment","Interested-Will Enroll","School Visit Done"]
        ,"cold":["Added in Waiting List","Enrolled in another school","Fees High","Junk/Invalid","Location not Convenient","Rejected","Schedule not Convenient","School Visit Done"],
        "enrolled":["Admission Taken"],
        "existing parents":["Already Enrolled"],
        "old leads":['Old lead'],
        "closed":['zxc']
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
    
    if(frm.doc.status)
    frm.set_df_property("lead_sub_status","options",subStatuses[frm.doc.status.toLowerCase()])
    $("textarea[data-fieldname='custom_cold_comment']").css({'height':'70'});
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
                    "school": frm.doc.center
                    }
                };
            });
        },
        status:function(frm){
          
            if(frm.doc.status)
            frm.set_df_property("lead_sub_status","options",subStatuses[frm.doc.status.toLowerCase()])
        }
    });
    

