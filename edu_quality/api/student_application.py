import frappe

import json
import requests
import datetime
import time

CONFIG ={
"WALSH_API_BASE":'https://testwalsh.walnutedu.in/indexCI.php',
"MGR_API_BASE":'https://test.walnutedu.in/indexCI.php',}


@frappe.whitelist()
def create_student_application(**args):
    if not args:
        raise frappe.exceptions.MandatoryError("Arguments are required")
    
    lead_doc_name = args.get('name')
    lead_application = frappe.get_doc('Lead',{"name":lead_doc_name})
    if not lead_application:
        return None
    student_application = frappe.get_doc(serialize_lead_to_application(lead_application)
    )
    created_mgr_lead=upload_to_mgr(student_application)
    student_application.lms_id = created_mgr_lead.get('ID')
    
    student_application.insert()
    frappe.msgprint(('Upload to MGR successful'))
    return student_application

@frappe.whitelist(allow_guest=True)
def update_stud_data(**data):
    data = data.get("Student").get("StudentInfoChange")
    
    existing_student_doc = frappe.get_list("Student Applicant",{'lms_id':data.get('lms_id'),'school':data.get('school_name')},ignore_permissions=True)
  
    if not existing_student_doc or len(existing_student_doc)==0:
        raise Exception("Student Doesnt exist")
    name = existing_student_doc[0].get('name')

    existing_student_doc = frappe.get_doc('Student Applicant',{'name':name})
    existing_student_doc.lms_status = data.get('lms_status')

    existing_student_doc.first_name = data.get('stud_f_name')
    existing_student_doc.last_name = data.get('stud_l_name')
    existing_student_doc.father_f_name = data.get('father_f_name')
    existing_student_doc.mother_f_name = data.get('mother_f_name')
    existing_student_doc.father_mobile_no = '+91'+data.get('father_mobile_no')
    existing_student_doc.father_email_address = data.get('father_email')
    existing_student_doc.gender = data.get('gender')
    existing_student_doc.date_of_birth = data.get('b_date')
    existing_student_doc.address_line_1 = data.get('bld_house')
    existing_student_doc.address_line_2 = data.get('sub_area')
    existing_student_doc.landmark = data.get('landmark')
    existing_student_doc.pincode = data.get('pin')
    existing_student_doc.city = data.get('city')
    existing_student_doc.state = data.get('state')
    existing_student_doc.country = data.get('country')
    existing_student_doc.bus_service_required = data.get('bus_service_required')
    existing_student_doc.admission_to = data.get('admission_to')
    existing_student_doc.academic_year = data.get('academic_year')
    existing_student_doc.stud_rte = data.get('stud_rte')
    existing_student_doc.caste = data.get('other_caste') or data.get('caste')
    existing_student_doc.religion =data.get('other_religion') or data.get('religion')
    existing_student_doc.subcaste = data.get('other_subcaste') or data.get('subcaste')
    existing_student_doc.student_mobile_number = data.get('student_sms_no')
    existing_student_doc.student_is_existingstudent = int(data.get('student_isexistingstudent'))
    existing_student_doc.student_existing_ref_number = data.get('student_existing_ref_number')
    existing_student_doc.is_sibling_in_school = int(data.get('student_bro_sis_inschoo'))
    existing_student_doc.school = data.get('school_name')
    existing_student_doc.blood_group =data.get('blood_group')
    existing_student_doc.catering = data.get('catering')
    existing_student_doc.aadhaar_card_number= data.get('adhar_card_no')
    existing_student_doc.parent_status = data.get('parent_status')
    existing_student_doc.single_parent_reason = data.get('single_parent_reason')
    existing_student_doc.nationality = data.get('nationality')
    existing_student_doc.allergies = data.get('other_allergies') or data.get('allergies')
    existing_student_doc.guardian_f_name = data.get('guardian_f_name')
    existing_student_doc.guardian_m_name= data.get('guardian_m_name')
    existing_student_doc.guardian_l_name= data.get('guardian_s_name')
    existing_student_doc.guardian_email_id= data.get('guardian_email_id')
    existing_student_doc.guardian_mobile_no= data.get('guardian_mobile_no')
    existing_student_doc.day_care_contact= data.get('day_care_contact')
    existing_student_doc.guardian_profession_other= data.get('guardian_profession_other')
    existing_student_doc.guardian_profession= data.get('guardian_profession')
    existing_student_doc.guardian_address1= data.get('guardian_bld_house')
    existing_student_doc.guardian_address2= data.get('guardian_sub_area')
    existing_student_doc.guardian_city= data.get('guardian_city')
    existing_student_doc.guardian_pin= data.get('guardian_pin')
    existing_student_doc.aadhaar_card_cert = data.get('adhar_card_cert')
    existing_student_doc.birth_cert = data.get('birth_cert')
    existing_student_doc.image = data.get('student_photo')

    existing_student_doc.father_m_name = data.get('father_m_name')
    existing_student_doc.father_s_name = data.get('father_s_name')
    existing_student_doc.father_education = data.get('father_education')
    existing_student_doc.father_profession = data.get('father_profession')
    existing_student_doc.father_annual_income = data.get('father_annual_income')
    existing_student_doc.father_company_name = data.get('father_company_name')
    existing_student_doc.father_designation = data.get('father_designation')
    existing_student_doc.father_office_address =data.get('father_office_address')

    existing_student_doc.mother_l_name = data.get('mother_l_name')
    existing_student_doc.mother_mobile_number = '+91'+data.get('mother_mobile_no')
    existing_student_doc.mother_email_id = data.get('mother_email_id')
    existing_student_doc.mother_education = data.get('mother_education')
    existing_student_doc.mother_profession = data.get('mother_profession')
    existing_student_doc.mother_annual_income = data.get('mother_annual_income')
    existing_student_doc.mother_company_name = data.get('mother_company_name')
    existing_student_doc.mother_designation = data.get('mother_designation')
    existing_student_doc.mother_office_address = data.get('mother_office_address')

    existing_student_doc.save(ignore_permissions=True)

    
def default(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    
def upload_to_mgr(doc):

    JSON = {
    "user":frappe.db.get_single_value("MGR Settings", "username"),
    "password":frappe.utils.password.get_decrypted_password(
            "MGR Settings", "MGR Settings", "password"
        ),
    "school_name":doc.get('school'),
    "first_name":doc.get('first_name'),
    "last_name":doc.get('last_name'),
    "mother_name":doc.get('mother_f_name'),
    "father_name":doc.get('father_f_name'),
    "father_mobile_number": doc.get("father_mobile_no"),
    "father_email_address":doc.get("father_email"),
    "gender":doc.get("gender"),
    "date_of_birth":doc.get("date_of_birth"),
    "address1":doc.get("address_line_1"),
    "address2":doc.get("address_line_2"),
    "pin":doc.get("pincode"),
    "city":doc.get("city"),
    "state":doc.get('state'),
    "bus_service_required":doc.get("bus_service_required"),
    "class":doc.get("program"),
    "RTE_student":doc.get("rte_student"),
    "preferred_batch_time":doc.get("batch_time"),
    "academic_year":doc.get("academic_year")
        }
    
    response = requests.post(
        url=f'{CONFIG.get("MGR_API_BASE")}/student_lms/post_student_lms_data',
        json= json.loads(json.dumps(JSON,default=default)) 
    )

    if("OK" not in response.text):
        frappe.msgprint((response.text))
        raise frappe.exceptions.DuplicateEntryError(response.text)
   
    data = json.loads(response.text)
    return data



def serialize_lead_to_application(doc: dict):
    if not doc:
        return {}
    
    fees_structure = frappe.db.get_value("Fee Structure",{'program':doc.get('class'),'school':doc.get('center'),'academic_year':doc.get('academic_year')},"name")
    return {
        'doctype':"Student Applicant",
        'first_name':doc.get('first_name'),
        'school':doc.get('center'),
        'academic_year':doc.get('academic_year'),
        'fee_structure':fees_structure,
        'student_email_id':f'test_only{str(time.time())}@yopmail.com',
        'program':doc.get('class'),
            'father_f_name':doc.get('fathers_name'),
            'preferred_batch_time':doc.get('preferred_batch_time'),
             'batch_time':doc.get('preferred_batch_time'),
            'gender':doc.get('gender'),
            'address_line_2':doc.get('address2'),
            'address_line_1':doc.get('address'),
            'country':doc.get('country'),
            'pincode':doc.get('pincode'),
            'state':doc.get('state'),
            'last_name':doc.get('last_name'),
            'mother_f_name':doc.get('mothers_name'),
            'date_of_birth':doc.get('date_of_birth'),
            'father_email':doc.get('fathers_email'),
            'mother_mobile_number':doc.get('mothers_phone'),
            'father_mobile_no':doc.get('fathers_phone'),
            'bus_service_required':doc.get('bus_service_required')
            }
    