import random
import string

import frappe
import requests
from frappe.auth import LoginManager

from edu_quality.public.py.utils import remove_indian_country_code


def generate_otp():
	# Generate a 6-digit OTP
	otp = "".join(random.choices(string.digits, k=4))
	return otp


def create_otp(email):
	if not email:
		return False

	# Assuming the email address is valid, you can use it directly as the cache key
	cache = frappe.cache()
	key = "otp_" + email
	otp = generate_otp()

	# Cache the OTP
	cache.set_value(key, otp)

	return otp


@frappe.whitelist(allow_guest=True)
def send_otp_to_email_address(email_address):
	try:
		if not email_address:
			return False

		# Generate OTP using create_otp function
		otp = create_otp(email_address)

		template_name = "Email Update OTP"
		email_template = frappe.get_doc("Email Template", template_name)
		content = frappe.render_template(
			email_template.get("response_html") or email_template.get("response"),
			{"otp": otp},
		)
		email_args = {
			"recipients": [email_address],
			"subject": email_template.get("subject"),
			"message": content,
		}

		frappe.sendmail(**email_args)
	except Exception as e:
		frappe.log_error("Error sending OTP email", str(e))
		return False


@frappe.whitelist(allow_guest=True)
def verify_otp(otp, email):
	try:
		if match_otp(email, otp):
			# Your verification logic here, for example:
			# Verify the OTP and perform necessary actions
			print("OTP verification successful for email:", email)
			return {
				"success": True,
				"message": "OTP verification successful",
			}
		else:
			return {
				"error": True,
				"error_type": "invalid_otp",
				"error_message": "Invalid OTP",
			}
	except Exception as e:
		return {
			"error": True,
			"error_type": "server_error",
			"error_message": str(e),
		}


@frappe.whitelist(allow_guest=True)
def verify_otp_mobile(otp, phone_no, push_token=None, form_link=None):
	try:
		wa_phone_no = generate__phone_otp(phone_no)
		phone_with_country_code = "+" + wa_phone_no
		guardian_number = remove_indian_country_code(phone_with_country_code)

		if match_otp(wa_phone_no, otp):
			guardian = get_guardian_number(guardian_number)
			user = frappe.get_cached_doc("User", guardian.user)
			login_manager = LoginManager()
			login_manager.login_as(user.name)

			if form_link:
				form_link = get_student_form(guardian)

			if push_token:
				save_push_notification_token(push_token, user.name)

			# key = "walsh_otp" + wa_phone_no
			# frappe.cache.delete_value(key)

			return {
				"success": True,
				"message": "Login Successful",
				"form_link": form_link,
			}

		return {
			"error": True,
			"error_type": "invalid_otp",
			"error_message": "Invalid OTP",
		}
	except Exception as e:
		return {"error": True, "error_type": "server_error", "error_message": str(e)}


def save_push_notification_token(push_token, user_id=None):
	user_id = user_id or frappe.session.user
	has_token = frappe.db.exists("Mobile Push Token", {"token": push_token, "user_id": user_id})
	if not has_token:
		frappe.get_doc({"doctype": "Mobile Push Token", "token": push_token, "user_id": user_id}).insert(
			ignore_permissions=True
		)


def match_otp(email, otp):
	cache = frappe.cache()
	key = "otp_" + email
	cache_otp = cache.get_value(key)

	return otp == cache_otp


def match_otp_mobile(mobile_number, otp):
	cache = frappe.cache()
	key = "wo" + mobile_number
	cache_otp = cache.get_value(key)
	frappe.logger("otp").exception("verify-" + key)
	frappe.logger("otp").exception(cache_otp)

	# print(wa_phone_no, "otp", otp, "cache_otp", cache_otp)
	return otp == cache_otp


def generate__phone_otp(phone_no):
	if not phone_no:
		return False
	if phone_no.startswith("+"):
		phone_no = phone_no[1:]
	if len(phone_no) == 10:
		phone_no = "91" + phone_no

	# check if all characters are numeric
	if not phone_no.isdigit():
		return False
	return phone_no


def create__phone_otp(wa_phone_no):
	otp = ""
	for _ in range(4):
		otp += str(random.randint(1, 9))
	cache = frappe.cache()
	key = "wo" + wa_phone_no
	# frappe.cache.delete_value(key)
	frappe.logger("otp").exception("generate-" + key)
	frappe.logger("otp").exception(otp)
	cache.set_value(key, otp)
	val = cache.get_value(key)
	frappe.logger("otp").exception("get-" + val)
	return otp


@frappe.whitelist(allow_guest=True)
def send_otp_to_mobile_number(mobile_number):
	wa_phone_no = generate__phone_otp(mobile_number)
	if not wa_phone_no:
		return {
			"error": True,
			"error_type": "invalid_phone_number",
			"error_message": "Invalid Phone Number",
		}

	phone_with_country_code = "+" + str(wa_phone_no)
	otp = create_otp(wa_phone_no)
	send_otp_to_sms(phone_with_country_code, otp)


def send_otp_to_sms(full_phone_no, otp):
	api_key = frappe.conf.get("sms_api_key")
	app_name = frappe.conf.get("sms_app_name") or "the app"
	message = (
		f"OTP is {otp} for logging into {app_name}. "
		+ "Valid till 10 min.\nDo not share OTP for security reasons."
	)
	template_id = frappe.conf.get("sms_login_template_id")
	sender = frappe.conf.get("sms_sender")
	encoded_message = requests.utils.quote(message)
	url = f"http://smssolution.net.in/api/v4/?api_key={api_key}&method=sms&message={encoded_message}\
    &to={full_phone_no}&sender={sender}&template_id={template_id}"
	response = requests.post(url)
	response = response.json()
	return response


def get_guardian_number(guardian_number):
	if frappe.db.exists("Guardian", {"mobile_number": guardian_number}):
		guardian = frappe.get_cached_doc("Guardian", {"mobile_number": guardian_number})
		return guardian
	elif frappe.db.exists("Guardian", {"custom_secondary_mobile_number": guardian_number}):
		guardian = frappe.get_cached_doc("Guardian", {"custom_secondary_mobile_number": guardian_number})
		return guardian
	return None


def get_student_form(doc):
	student_forms = []
	applicants = frappe.db.get_all(
		"Student Guardian",
		{"guardian": doc.name, "parenttype": "Student Applicant"},
		"parent",
	)
	link = frappe.utils.get_url() + "/walnut-school-student-application/"
	for applicant in applicants:
		student = frappe.db.get_value("Student", {"student_applicant": applicant.parent}) or applicant.parent
		student_forms.append({"student": student, "link": link + applicant.parent + "/edit"})
	return student_forms
