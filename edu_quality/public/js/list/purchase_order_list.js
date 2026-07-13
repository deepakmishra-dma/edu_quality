frappe.listview_settings["Purchase Order"] = {
  get_indicator: function (doc) {
    if (doc.status === "Closed") {
      return [__("Closed"), "green", "status,=,Closed"];
    } else if (doc.status === "On Hold") {
      return [__("On Hold"), "orange", "status,=,On Hold"];
    } else if (doc.status === "Delivered") {
      return [__("Delivered"), "green", "status,=,Closed"];
    } else if (doc.status !== "Closed") {
      let printed_count = doc.custom_printed_count;
      let total_count = doc.custom_total_items;

      if (printed_count == 0) {
        return [
          __("To Receive and Bill"),
          "orange",
          "per_received,<,100|per_billed,<,100|status,!=,Closed",
        ];
      } else if (printed_count === total_count) {
        return [__("Printed"), "green", "status,!=,Closed"];
      } else {
        return [__("Partially Printed"), "orange", "status,!=,Closed"];
      }
    } else if (flt(doc.per_received, 2) < 100 && doc.status !== "Closed") {
      if (flt(doc.per_billed, 2) < 100) {
        return [
          __("To Receive and Bill"),
          "orange",
          "per_received,<,100|per_billed,<,100|status,!=,Closed",
        ];
      } else {
        return [
          __("To Receive"),
          "orange",
          "per_received,<,100|per_billed,=,100|status,!=,Closed",
        ];
      }
    } else if (
      flt(doc.per_received, 2) >= 100 &&
      flt(doc.per_billed, 2) < 100 &&
      doc.status !== "Closed"
    ) {
      return [
        __("To Bill"),
        "orange",
        "per_received,=,100|per_billed,<,100|status,!=,Closed",
      ];
    } else if (
      flt(doc.per_received, 2) >= 100 &&
      flt(doc.per_billed, 2) == 100 &&
      doc.status !== "Closed"
    ) {
      return [
        __("Completed"),
        "green",
        "per_received,=,100|per_billed,=,100|status,!=,Closed",
      ];
    }
  },
};
