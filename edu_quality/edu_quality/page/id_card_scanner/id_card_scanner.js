
async function folderExists(parent, newFolder) {
	const formData = new FormData()
	formData.append('file_name', newFolder)
	formData.append('folder', parent)

	try {

		let res = await fetch(`/api/resource/File/${parent}/${newFolder}`)
		if (res.status === 404) {
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
	catch (e) {

	}

}
function uploadImage(image, folder, image_name) {

	return fetch(image).then((res) => res.blob()).then((blob) => {
		const formData = new FormData();
		const file = new File([blob], "image.jpg");

		formData.append('file', file, image_name)
		formData.append('folder', "home/" + folder)
		formData.append('is_private', 1)
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

		return res.json()
	}).then(({ message }) => message.file_url).catch((error) => {
		nativeInterface.logToNative(error)
	})
}

const checkIfRefNoExists = async (academicYear, school, refNo) => {
	try {
		let res = await fetch(`/api/resource/Student?fields=["name","class_details"]&filters=[["school","like","${school}"],["reference_number","=","${refNo}"]]`)
		const student = (await res.json())?.data?.[0]
		if (!student) throw new Error("Student doesn't exist")
		const enrollmentRes = await fetch(`/api/resource/Program Enrollment?fields=["name","custom_id_card"]&filters=[["student","like","${student.name}"],["academic_year","=","${academicYear}"]]`)
		const programEnrollment = (await enrollmentRes.json())?.data?.[0]
		if (!programEnrollment) throw new Error("Enrollment doesn't exist")

		const data = await fetch(`/api/resource/Student ID Card/${programEnrollment.custom_id_card}`)
		const idCardData = await data.json()
		if (!idCardData) throw new Error("ID Card doesn't exist")
		return idCardData.data
	}
	catch (e) {
		frappe.msgprint(e.message)
	}

}

const updateIDCard = async (idCard, body) => {
	let res = await fetch(`/api/resource/Student ID Card/${idCard}`, {
		method: "PUT",
		body: JSON.stringify(body)
	})
	let data = res.json()
	return data.data
}

frappe.pages['id-card-scanner'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'ID Card Scanner',
		single_column: true
	});
	// let field = page.add_field({
	// 	label: 'School',
	// 	fieldname: 'school',
	// 	fieldtype: 'Link',
	// 	options: "School",
	// 	reqd: true
	// })
	const el = document.querySelector('.container.page-body')
	var image = null
	const d = make_fieldgroup(el, [
		{
			label: 'School',
			fieldname: 'school',
			fieldtype: 'Link',
			options: "School",
			reqd: true
		},
		{
			label: 'Academic Year',
			fieldname: 'academic_year',
			fieldtype: 'Link',
			options: "Academic Year",
			reqd: true
		},
		{
			label: 'Scanner',
			fieldname: 'scanbtn',
			fieldtype: 'Button',
			click: async () => {
				const images = await nativeInterface.execute('openWebViewScanner')
				const [academicYear, school, refNo] = images?.data?.split("/")
				d.set_value("refNo", refNo)
				d.set_value("academic_year", academicYear)
				d.set_value("school", school)
				checkIfRefNoExists(academicYear, school, refNo)
			}
		},
		{
			label: 'Enter Ref No',
			fieldname: 'refNo',
			fieldtype: 'Data',
			reqd: true
		}, {
			label: 'Reset',
			fieldname: 'reset_btn',
			fieldtype: 'Button',
			click: () => {
				d.set_value("refNo", '')
				d.set_value("earlier_timestamp", "")
				d.set_value("earlier_status", "")
				d.set_value("earlier_photo_id", "")
			}

		},

		{
			label: 'Check',
			fieldname: 'check_btn',
			fieldtype: 'Button',
			click: async function () {
				console.log(d)
				academicYear = d['fields_dict']['academic_year']['input'].value
				school = d['fields_dict']['school']['input'].value
				refNo = d['fields_dict']['refNo']['input'].value
				const idCard = checkIfRefNoExists(academicYear, school, refNo)
				if (idCard) {
					d.set_value('earlier_timestamp', idCard.photo_taken_time)
					d.set_value('earlier_photo_id', idCard.id_card_given_on)
					d.set_value('earlier_status', idCard.status)

				}
			}

		},
		{
			label: 'Earlier Photo Taken On',
			fieldname: 'earlier_timestamp',
			fieldtype: 'Data',
			read_only: true,
		}, {
			label: 'Earlier Photo Status',
			fieldname: 'earlier_status',
			fieldtype: 'Data',
			read_only: true,
		},
		{
			label: 'Earlier ID Given on',
			fieldname: 'earlier_photo_id',
			fieldtype: 'Date',
			read_only: true,
		},
		{
			label: 'Take photo',
			fieldname: 'take_photo',
			fieldtype: 'Button',
			read_only: true,
			click: async () => {
				const images = await nativeInterface.execute('openWebViewCamera', {
					multiple: false
				})
				const [img] = images;
				image = 'data:image/jpg;base64,' + img.base64
				d.set_value('photo', `<img src = '${image}' style ='height:100px;width:100px;object-fit:contain;'></img>`)
			}
		},
		{
			options: "<img src = '/private/files/2.png' style ='height:100px;width:100px;object-fit:contain;'></img>",
			label: '',
			fieldname: 'photo',
			fieldtype: 'HTML',
			read_only: true,
		},
	])
	// page.add_field({
	// 	label: 'Upload',
	// 	class: 'btn btn-primary btn-sm primary-action',
	// 	fieldname: 'upload_btn',
	// 	fieldtype: 'Button',
	// click: ,
	// })
	page.add_inner_button('Upload', async function () {
		const academicYear = d['fields_dict']['academic_year']['input'].value
		const school = d['fields_dict']['school']['input'].value
		const refNo = d['fields_dict']['refNo']['input'].value

		const idCard = await checkIfRefNoExists(academicYear, school, refNo)
		if (idCard.status.toLowerCase() === "pending") return
		if (!image || !idCard) return
		await folderExists("Home", `${school}-${academicYear}`)
		const img = await uploadImage(image, `${school}-${academicYear}`, `${refNo}-${idCard.name}`)
		image = ""
		const payload = { ...idCard, photo_taken: img, status: "CLICKED", "photo_taken_time": new Date() }
		const data = await updateIDCard(idCard.name, payload)

		frappe.call({
			method: "edu_quality.api.google_drive_upload.upload_file",
			args: {
				file_url: img,
				folder_name: `${school}-${academicYear}`,
				type: "POST",
			}, callback: () => {

			}
		})

	})

}

function make_fieldgroup(parent, ddf_list) {
	fg = new frappe.ui.FieldGroup({
		"fields": ddf_list,
		"parent": parent
	});
	fg.make();
	console.log(fg)
	return fg

}

function add_fields_page(page, fields) {
	if (fields.length > 0) {
		for (let i of fields) {
			page.add_field({ i })
		}
	}
	else {
		page.add_field(fields)
	}
}