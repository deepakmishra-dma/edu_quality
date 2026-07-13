frappe.ui.form.on("Purchase Receipt", {
  refresh(frm) {
    frm.get_field("custom_print").onclick = function () {
      var myImage = frm.doc.custom_qr_code_base;
      var image = new Image();
      image.src = myImage;
      var myWindow = window.open("", "Image");
      myWindow.document.body.appendChild(image);
      myWindow.print();
    };
    frm.get_field("custom_download").onclick = function () {
      var a = document.createElement("a");
      a.href = frm.doc.custom_qr_code_base;
      a.download = "Image.png";
      a.click();
      a.remove();
    };
  },
});
