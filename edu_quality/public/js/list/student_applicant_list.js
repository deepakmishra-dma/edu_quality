frappe.listview_settings["Student Applicant"] = {
  hide_name_column: true,
  button: {
    show(doc) {
      return doc.student_mobile_number;
    },
    get_label() {
      return '<img src="https://static.vecteezy.com/system/resources/thumbnails/000/423/339/small/Multimedia__2850_29.jpg" width="14",height="14">';
    },
    get_description(doc) {
      return __("Copy {0}", [`${doc.student_mobile_number}`]);
    },
    action(doc) {
      var tempTextarea = document.createElement("textarea");
      tempTextarea.value = doc.student_mobile_number;
      document.body.appendChild(tempTextarea);
      tempTextarea.select();
      document.execCommand("copy");
      document.body.removeChild(tempTextarea);
    },
  },
  formatters: {
    program(val) {
      return val.split("-")[0];
    },
  },
};
