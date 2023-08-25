frappe.listview_settings['Lead'] = {
    hide_name_column: true,
    button: {
        show(doc) {
            return doc.fathers_phone;
        },
        get_label() {
            return 'Copy Mobile No';
        },
        get_description(doc) {
            return __('Copy {0}', [`${doc.fathers_phone}`])
        },
        action(doc) {
            var tempTextarea = document.createElement('textarea');
            tempTextarea.value = doc.fathers_phone;
            document.body.appendChild(tempTextarea);
            tempTextarea.select();
            document.execCommand('copy');
            document.body.removeChild(tempTextarea);
            frappe.msgprint(__("Phone numbers copied to clipboard: ") + doc.fathers_phone);
        }
    },
    formatters: {
        title(val) {
            return val.bold();
        },
        public(val) {
            return val ? 'Yes' : 'No';
        }
    }
}