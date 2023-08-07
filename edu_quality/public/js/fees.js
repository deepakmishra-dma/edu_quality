frappe.ui.form.on('Fees', {
    refresh: function(frm) {
        frm.add_custom_button(__('Add Discount'), function(){
        let d = new frappe.ui.Dialog({
        title: 'Add Discount',
        fields: [
            {
                label: 'Discount Name',
                fieldname: 'discount_name',
                fieldtype: 'Link',
                options: "Discount Configuration",
                get_query: function () {
    					return {
    						doctype: 'Discount Configuration',
    						filters: {
    							fee_structure: frm.doc.fee_structure,
    							type: "One Time"
    						},
    					};
				    }
            }
        ],
        size: 'large',
        primary_action_label: 'Submit',
        primary_action(values) {
            frappe.call({
                method: "edu_quality.public.py.discount.add_discount",
                type: "POST",
                args: {
                    discount: values.discount_name,
                    fee_name: frm.doc.name
                },
                callback: function(response) {
                    frappe.msgprint({
                        title: __("Add Discount"),
                        message: __(response.message),
                        primary_action: {
                            label: __("OK"),
                            action: function() {
                                frappe.hide_msgprint();
                            }
                        }
                    });
                    frm.reload_doc();
                }
            });
            d.hide();
        }
    });
    
    d.show();

    }, __("Discount"));
    frm.add_custom_button(__('Remove Discount'), function(){
        let d = new frappe.ui.Dialog({
        title: 'Remove Discount',
        fields: [
            {
                label: 'Discount Name',
                fieldname: 'discount_name',
                fieldtype: 'Link',
                options: "Discount Configuration",
                get_query: function () {
    					return {
    						doctype: 'Discount Configuration',
    						filters: {
    							fee_structure: frm.doc.fee_structure,
    							type: "One Time"
    						},
    					};
				    }
            }
        ],
        size: 'large',
        primary_action_label: 'Submit',
        primary_action(values) {
            frappe.call({
                method: "edu_quality.public.py.discount.remove_discount",
                type: "POST",
                args: {
                    discount: values.discount_name,
                    fee_name: frm.doc.name
                },
                callback: function(response) {
                    frappe.msgprint({
                        title: __("Remove Discount"),
                        message: __(response.message),
                        primary_action: {
                            label: __("OK"),
                            action: function() {
                                frappe.hide_msgprint();
                            }
                        }
                    });
                    frm.reload_doc();
                }
            });
            d.hide();
        }
    });
    
    d.show();
    }, __("Discount"));
  }
});