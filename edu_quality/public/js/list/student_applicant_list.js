frappe.listview_settings['Student Applicant'] = {
    hide_name_column: true,
    button: {
        show(doc) {
            return doc.student_mobile_number;
        },
        get_label() {
            return 'Copy Mobile No';
        },
        get_description(doc) {
            return __('Copy {0}', [`${doc.student_mobile_number}`])
        },
        action(doc) {
            var tempTextarea = document.createElement('textarea');
            tempTextarea.value = doc.student_mobile_number;
            document.body.appendChild(tempTextarea);
            tempTextarea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextarea);
            frappe.msgprint(__("Phone numbers copied to clipboard: ") + doc.student_mobile_number);
        }
    },
    formatters: {
        program(val) {
            return val.split("-").slice(-2)[0];
        }
    }
}