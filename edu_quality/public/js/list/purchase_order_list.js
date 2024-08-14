frappe.listview_settings['Purchase Order'] = {
    get_indicator: function (doc) {
		if (doc.status === "Closed") {
			return [__("Closed"), "green", "status,=,Closed"];
		} else if (doc.status === "On Hold") {
			return [__("On Hold"), "orange", "status,=,On Hold"];
		} else if (doc.status === "Delivered") {
			return [__("Delivered"), "green", "status,=,Closed"];
		} else if(doc.status !== "Closed"){
            let printed_count=0;
            let total_count=0;
            doc.items.forEach(element => {
                if(element.printed == 1){
                    printed_count = printed_count + 1;
                }
                total_count = total_count + 1;
            });
            if(printed_count == 0){
                return [__("To Receive and Bill"), "orange",
                "per_received,<,100|per_billed,<,100|status,!=,Closed"];
            }
            else if(printed_count == total_count){
                return [_("Printed"),"green","status,!=,Closed"]

            }
            else{
                return [_("Partially Printed"),"orange","status,!=,Closed"]
            }
        
        }else if (flt(doc.per_received, 2) < 100 && doc.status !== "Closed") {
			if (flt(doc.per_billed, 2) < 100) {
				return [__("To Receive and Bill"), "orange",
					"per_received,<,100|per_billed,<,100|status,!=,Closed"];
			} else {
				return [__("To Receive"), "orange",
					"per_received,<,100|per_billed,=,100|status,!=,Closed"];
			}
		} else if (flt(doc.per_received, 2) >= 100 && flt(doc.per_billed, 2) < 100 && doc.status !== "Closed") {
			return [__("To Bill"), "orange", "per_received,=,100|per_billed,<,100|status,!=,Closed"];
		} else if (flt(doc.per_received, 2) >= 100 && flt(doc.per_billed, 2) == 100 && doc.status !== "Closed") {
			return [__("Completed"), "green", "per_received,=,100|per_billed,=,100|status,!=,Closed"];
		}
	}

};