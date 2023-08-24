
async function folderExists(parent,newFolder){
    const formData = new FormData()
    formData.append('file_name',newFolder)
    formData.append('folder',parent)

    try{
    
   let res =  await fetch(`/api/resource/File/${parent}/${newFolder}`)
   if(res.status===404){
     await fetch("/api/method/frappe.core.api.file.create_new_folder", {
        method: 'POST',
        headers: (() => {
            const headers = new Headers()
            headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
            return headers;
        })(),
        body: formData
    })
   }
   return (await res.json())

    }
    catch(e){

    }

}
function uploadImage(image,frm) {

    return fetch(image).then((res) => res.blob()).then((blob) => {
        const formData = new FormData();
        const file = new File([blob], "image.jpg");
   
        formData.append('file', file, "image.jpg")
        formData.append('folder',"home/"+frm.doc.name)
        nativeInterface.logToNative(formData)
        return fetch("/api/method/upload_file", {
            method: 'POST',
            headers: (() => {
                const headers = new Headers()
                headers.append('X-Frappe-CSRF-Token', frappe.csrf_token)
                return headers; 
            })(),
            body: formData
        })
    }
    ).then((res) => {
      
      return res.json()}).then(({message}) => message.file_url).catch((error)=>{
            nativeInterface.logToNative(error)
        })
}

frappe.ui.form.on("Carnival Event", {
    refresh:function(frm){

     setTimeout(()=>{
      
            frm.add_custom_button(__("Upload Images"), async function() {
             const images = await nativeInterface.execute('openWebViewCamera',{multiple:true, preferredCameraType:'rear'})
                   await  folderExists('Home',frm.doc.name)

                     Promise.allSettled([images.map((img)=>uploadImage('data:image/jpg;base64,' + img.base64,frm))]).then(
                        frappe.msgprint({
                            title: __('Successful'),
                            message: __('Upload Completed'),
                        
                        })
                     )
                   
                   
                })
              
        

            
        
            })
    },
 
     school: function(frm) {

           frm.set_query("class", function() {
           return {
                "filters": {
                    "school": frm.doc.school
                    }
                };
            });
        }
    });
    