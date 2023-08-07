import frappe
import mysql.connector


def migrate_mysql(database):
    frappe.flags.in_import = False
    frappe.msgprint("Migrating....")
    config = frappe.get_site_config()
    mysql_host = config.get("mysql_host")
    mysql_user = config.get("mysql_user")
    mysql_password = config.get("mysql_password")
    table_name = config.get("table_name")
    doctype = config.get("doctype")
    sync_data(mysql_host, mysql_user, mysql_password, database, table_name, doctype)


def sync_data(host, user, password, database, mysql_table, doctype):
    try:
        mysql_connection = mysql.connector.connect(
            host=host, user=user, password=password, database=database
        )

        mysql_query = f"SELECT * FROM {mysql_table}"

        mysql_cursor = mysql_connection.cursor()
        mysql_cursor.execute(mysql_query)

        column_names = [desc[0] for desc in mysql_cursor.description]

        mysql_rows = mysql_cursor.fetchall()

        # Iterate over the rows and create Frappe records
        for row in mysql_rows:
            frappe_data = {}
            for i, value in enumerate(row):
                frappe_data[column_names[i]] = value

            form_code = frappe_data.get("form_code")
            first_name = frappe_data.get("first_name")
            middle_name = frappe_data.get("middle_name")
            last_name = frappe_data.get("last_name")
            date_of_birth = frappe_data.get("b_date")
            blood_group = (
                ""
                if frappe_data.get("blood_group") == "Other"
                else frappe_data.get("blood_group")
            )
            student_mobile_number = frappe_data.get("student_primary_contact_number")
            gender = frappe_data.get("gender")
            nationality = frappe_data.get("nationality")
            address_line_1 = frappe_data.get("bld_house")
            survey_number = frappe_data.get("survey_number")
            sub_area = frappe_data.get("sub_area")
            road = frappe_data.get("road")
            area = frappe_data.get("area")
            address_line_2 = f"{survey_number}, {sub_area}, {road}, {area}"
            pincode = frappe_data.get("pin")
            city = frappe_data.get("city")
            state = frappe_data.get("state")

            countries = frappe.get_all("Country")
            countries = [d["name"] for d in countries]

            country = (
                "India"
                if frappe_data.get("country") not in countries
                else frappe_data.get("country")
            )

            date_of_leaving = frappe_data.get("leaving_date")
            joining_date = frappe_data.get("joining_date")
            if date_of_leaving is not None:
                joining_date = date_of_leaving - frappe.utils.datetime.timedelta(
                    days=365
                )
            else:
                joining_date = ""

            student_name = (
                f"{first_name} {'' if middle_name==None else middle_name} {last_name}"
            )
            student_email_id = f"{str(first_name).lower().replace(' ', '')}{student_mobile_number[:5] if student_mobile_number else ''}@walnut.edu"
            try:
                if not frappe.db.exists(doctype, {"form_code": form_code}):
                    new_doc = frappe.get_doc(
                        {
                            "form_code": form_code,
                            "enabled": 1,
                            "first_name": first_name,
                            "middle_name": middle_name,
                            "last_name": last_name,
                            "date_of_birth": date_of_birth,
                            "blood_group": blood_group,
                            "student_mobile_number": student_mobile_number,
                            "gender": gender,
                            "nationality": nationality,
                            "address_line_1": address_line_1,
                            "address_line_2": address_line_2,
                            "pincode": pincode,
                            "city": city,
                            "state": state,
                            "country": country,
                            "student_email_id": student_email_id,
                            "joining_date": joining_date,
                            "date_of_leaving": date_of_leaving,
                            "student_name": student_name,
                            "doctype": doctype,
                        }
                    )
                    new_doc.insert(ignore_permissions=True)

                else:
                    doc = frappe.get_doc({"doctype": doctype, "form_code": form_code})
                    doc.update(
                        {
                            "enabled": 1,
                            "first_name": first_name,
                            "middle_name": middle_name,
                            "last_name": last_name,
                            "date_of_birth": date_of_birth,
                            "blood_group": blood_group,
                            "student_mobile_number": student_mobile_number,
                            "gender": gender,
                            "nationality": nationality,
                            "address_line_1": address_line_1,
                            "address_line_2": address_line_2,
                            "pincode": pincode,
                            "city": city,
                            "state": state,
                            "country": country,
                            "joining_date": joining_date,
                            "date_of_leaving": date_of_leaving,
                            "student_name": student_name,
                        }
                    )
                    doc.save(ignore_permissions=True)

                print(f"Frappe document created: {new_doc.name}")
            except Exception as ex:
                print(f"Error Occured: {repr(ex)}")
            frappe.db.commit()
        return "Success"
    except Exception as ex:
        return f"Error Occured: {repr(ex)}"
    finally:
        # Close the MySQL connection
        mysql_cursor.close()
        mysql_connection.close()
