frappe.listview_settings['Lead'] = {
    hide_name_column: true,
    button: {
        show(doc) {
            return doc.fathers_phone;
        },
        get_label() {
            return '<img src="https://static.vecteezy.com/system/resources/thumbnails/000/423/339/small/Multimedia__2850_29.jpg" width="14",height="14">';
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
        }
    }
}