frappe.pages['cmap-creation-tool'].on_page_load = function (wrapper) {
	console.log('Loading cmap-creation-tool component');
	const builder = document.createElement('cmap-creation-tool');
	console.log("builder", builder)

	window.location = '/cmap-tool';

	wrapper.appendChild(builder);
	console.log('cmap-creation-tool component appended');
}
